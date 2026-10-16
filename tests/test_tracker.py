import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from src.kwork_notifier.tracker import DeliveryHistory, send_new_projects, track_new_projects


def project(project_id):
    return SimpleNamespace(
        id=project_id, title=f"Project {project_id}", price=5000,
        description="First line<br>Second &amp; third", offers=3,
    )


class FakeBot:
    def __init__(self, fail_once_for=None):
        self.fail_once_for = fail_once_for
        self.messages = []

    async def send_message(self, chat_id, text):
        if self.fail_once_for and f"projects/{self.fail_once_for}/view" in text:
            self.fail_once_for = None
            raise ConnectionError("Telegram unavailable")
        self.messages.append((chat_id, text))


class TrackerTest(unittest.IsolatedAsyncioTestCase):
    async def test_sends_the_whole_batch_in_id_order(self):
        bot = FakeBot()
        sent = await send_new_projects([project(3), project(1), project(2), project(2)], bot, -42, DeliveryHistory())

        self.assertEqual(sent, 3)
        for (chat_id, message), expected_id in zip(bot.messages, [1, 2, 3]):
            self.assertEqual(chat_id, -42)
            self.assertIn(f"Title: Project {expected_id}", message)
            self.assertIn("First line\nSecond & third", message)

    async def test_overlapping_polls_do_not_resend_delivered_projects(self):
        bot, history = FakeBot(), DeliveryHistory()
        await send_new_projects([project(1), project(2)], bot, -42, history)
        sent = await send_new_projects([project(2), project(3)], bot, -42, history)

        self.assertEqual(sent, 1)
        self.assertEqual(len(bot.messages), 3)

    async def test_failed_send_can_be_retried_without_resending_successes(self):
        bot, history = FakeBot(fail_once_for=2), DeliveryHistory()
        with self.assertRaises(ConnectionError):
            await send_new_projects([project(3), project(1), project(2)], bot, -42, history)

        self.assertIn(1, history)
        self.assertNotIn(2, history)
        self.assertNotIn(3, history)

        sent = await send_new_projects([project(1), project(2), project(3)], bot, -42, history)
        self.assertEqual(sent, 2)
        self.assertEqual(len(bot.messages), 3)

    async def test_cancellation_does_not_acknowledge_a_delivery(self):
        bot, history = SimpleNamespace(send_message=AsyncMock(side_effect=asyncio.CancelledError)), DeliveryHistory()
        with self.assertRaises(asyncio.CancelledError):
            await send_new_projects([project(1)], bot, -42, history)
        self.assertNotIn(1, history)

    async def test_empty_batch_sends_nothing(self):
        bot = FakeBot()
        self.assertEqual(await send_new_projects([], bot, -42, DeliveryHistory()), 0)
        self.assertEqual(bot.messages, [])

    async def test_polling_recovers_from_a_send_failure(self):
        bot = FakeBot(fail_once_for=2)
        api = SimpleNamespace(get_projects=AsyncMock(return_value=[project(1), project(2), project(3)]))
        settings = SimpleNamespace(categories_ids=(5, 7), group_chat_id=-42, poll_interval_seconds=60)

        with patch("src.kwork_notifier.tracker.asyncio.sleep", new=AsyncMock(side_effect=[None, asyncio.CancelledError])):
            with self.assertLogs("kwork-tracker", level="INFO"):
                with self.assertRaises(asyncio.CancelledError):
                    await track_new_projects(api, bot, settings)

        self.assertEqual(api.get_projects.await_count, 2)
        api.get_projects.assert_awaited_with(categories_ids=[5, 7])
        self.assertEqual(len(bot.messages), 3)


class HistoryTest(unittest.TestCase):
    def test_keeps_only_the_last_delivered_ids(self):
        history = DeliveryHistory(limit=3)
        for project_id in [1, 2, 2, 3, 4]:
            history.remember(project_id)
        self.assertNotIn(1, history)
        for project_id in [2, 3, 4]:
            self.assertIn(project_id, history)

    def test_rejects_an_empty_history(self):
        with self.assertRaises(ValueError):
            DeliveryHistory(limit=0)


if __name__ == "__main__":
    unittest.main()
