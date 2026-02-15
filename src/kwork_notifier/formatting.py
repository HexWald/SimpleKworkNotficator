import html
import re

_BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)

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

def build_message(project) -> str:
    title = clean_text(project.title)
    description = clean_text(project.description)

    return (
        "New Project:\n"
        f"Title: {title}, Price: {project.price}₽\n"
        f"Description: {description}\n"
        f"Responses: {project.offers}{offers_label(project.offers)}\n"
        f"Link: https://kwork.ru/projects/{project.id}/view"
    )
