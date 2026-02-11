import logging
import asyncio
import configparser

from kwork import Kwork
from telegram import Bot

logging.basicConfig(level=logging.INFO)
config = configparser.ConfigParser(interpolation=None)
config.read('config.ini')

GROUP_CHAT_ID = config.get('Credentials', 'GROUP_ID')
TELEGRAM_TOKEN = config.get('Credentials', 'TELEGRAM_TOKEN')
LOGIN = config.get('Credentials', 'LOGIN')
PASSWORD = config.get('Credentials', 'PASSWORD')

last_project_id = None

def clean_description(description):

    description = description.replace('<br>', '\n')
    description = description.replace('-&gt;', '>')  # >
    description = description.replace('&lt;', '<')  # <
    description = description.replace('&amp;', '&')  # &
    description = description.replace('&quot;', '"')  # "
    description = description.replace('&apos;', "'")  # '

    return description

async def track_new_projects(api, bot):

    global last_project_id

    projects = await api.get_projects(categories_ids=[41, 80, 40, 255, 81])

    if projects:

        first_project = projects[0]

        offers_text = (
            " ( Actual! )" if first_project.offers < 5 else
            " ( 50/50 actual :/ )" if first_project.offers <= 10 else
            " ( Maybe not actual :( )"
        )

        cleaned_description = clean_description(first_project.description)
        cleaned_title = clean_description(first_project.title)

        await bot.send_message(GROUP_CHAT_ID,
                               f"New Project:\nTitle: {cleaned_title}, Price: {first_project.price}₽, Description: {cleaned_description}\nResponses: {first_project.offers}{offers_text}\nLink: https://kwork.ru/projects/{first_project.id}/view")
        last_project_id = first_project.id

    while True:
        projects = await api.get_projects(categories_ids=[41, 80, 40, 255, 81])

        if projects:
            current_project_id = projects[0].id
            if current_project_id != last_project_id:

                last_project_id = current_project_id
                new_project = projects[0]

                offers_text = (
                    " ( Actual! )" if first_project.offers < 5 else
                    " ( 50/50 actual :/ )" if first_project.offers <= 10 else
                    " ( Maybe not actual :( )"
                )

                cleaned_description = clean_description(new_project.description)
                cleaned_title = clean_description(new_project.title)

                await bot.send_message(GROUP_CHAT_ID,
                                       f"New Project:\nTitle: {cleaned_title}, Price: {first_project.price}₽, Description: {cleaned_description}\nResponses: {first_project.offers}{offers_text}\nLink: https://kwork.ru/projects/{first_project.id}/view")
        await asyncio.sleep(60)

async def main():

    api = Kwork(LOGIN, PASSWORD)
    bot = Bot(token=TELEGRAM_TOKEN)

    await track_new_projects(api, bot)

    await api.close()

if __name__ == "__main__":
    asyncio.run(main())