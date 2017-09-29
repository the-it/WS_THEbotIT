import re

from tools.bots import OneTimeBot

class REImporter(OneTimeBot):
    bot_name = 'REImporter'

    def __init__(self, wiki):
        OneTimeBot.__init__(self, wiki)

    def task(self):
        pass