import os

TMP_WIKI_BOT_PATH: str = "/tmp/.wiki_bot"


def get_data_path() -> str:
    if not os.path.exists(TMP_WIKI_BOT_PATH):
        os.mkdir(TMP_WIKI_BOT_PATH)
    return TMP_WIKI_BOT_PATH
