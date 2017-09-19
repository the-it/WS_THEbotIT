import re

from tools.bots import OneTimeBot

class REImporter(OneTimeBot):
    def __init__(self, wiki):
        OneTimeBot.__init__(self, wiki)
        self.bot_name = 'REImporter'

    def run(self):
        pass