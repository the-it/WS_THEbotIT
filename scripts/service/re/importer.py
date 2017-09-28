import re

from tools.bots import OneTimeBot

class REImporter(OneTimeBot):
    bot_name = 'REImporter'

    def __init__(self, main_wiki):
        OneTimeBot.__init__(self, main_wiki)

    def task(self):
        pass