__author__ = 'erik'

import sys
import os
from datetime import datetime
from authorlist

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep)

from tools.bots import PingBot, SaveExecution

if __name__ == "__main__":
    #daily bots
    bot = PingBot()
    with SaveExecution(bot):
        bot.run()

    if datetime.now().weekday() == 6:
        #tasks for sunday
        with