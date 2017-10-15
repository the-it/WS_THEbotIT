from tools.bots import OneTimeBot


class REImporter(OneTimeBot):
    bot_name = 'REImporter'

    def __init__(self, wiki, debug):
        OneTimeBot.__init__(self, wiki, debug)

    def task(self):
        pass
