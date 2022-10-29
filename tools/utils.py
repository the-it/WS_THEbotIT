from pywikibot import Page


def save_if_changed(page: Page, text: str, change_msg: str):
    if text.rstrip() != page.text:
        page.text = text
        page.save(change_msg, botflag=True)
