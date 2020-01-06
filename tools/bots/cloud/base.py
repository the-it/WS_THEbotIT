import os

DATA_PATH: str = "/tmp/.wiki_bot"


def get_data_path() -> str:
    if not os.path.exists(DATA_PATH):
        os.mkdir(DATA_PATH)
    return DATA_PATH
