import re

from tools.bots import OneTimeBot

class REImporter(OneTimeBot):
    def __init__(self, main_wiki):
        OneTimeBot.__init__(self, main_wiki)
        self.bot_name = 'REImporter'

    def task(self):
        pass