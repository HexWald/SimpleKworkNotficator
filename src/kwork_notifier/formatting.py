import html
import re

_BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_MESSAGE_LIMIT = 4096

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = _BR_RE.sub("\n", text)
    text = html.unescape(text)
    return text.strip()

def offers_label(offers: int) -> str:
    if offers < 5:
        return " ( Actual! )"
    if offers <= 10:
        return " ( 50/50 actual :/ )"
    return " ( Maybe not actual :( )"


def _fit_text(text: str, byte_budget: int) -> str:
    encoded = text.encode("utf-16-le")
    if len(encoded) <= byte_budget:
        return text
    if byte_budget < 2:
        return ""
    shortened = encoded[:byte_budget - 2].decode("utf-16-le", errors="ignore").rstrip()
    return shortened + "…"


def build_message(project) -> str:
    prefix = "New Project:\nTitle: "
    between = f", Price: {project.price}₽\nDescription: "
    footer = (
        f"\nResponses: {project.offers}{offers_label(project.offers)}\n"
        f"Link: https://kwork.ru/projects/{project.id}/view"
    )
    budget = _MESSAGE_LIMIT * 2 - len((prefix + between + footer).encode("utf-16-le"))
    title = _fit_text(clean_text(project.title), budget)
    description = _fit_text(clean_text(project.description), budget - len(title.encode("utf-16-le")))
    return f"{prefix}{title}{between}{description}{footer}"
