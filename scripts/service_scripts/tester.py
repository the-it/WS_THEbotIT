import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep)

from pywikibot import Site
from scripts.service_scripts.create_magazine_GL import MagazinesGL
from tools.bots import SaveExecution

def run_bot(bot):
    with SaveExecution(bot):
        bot.run()

if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    run_bot(MagazinesGL(wiki=wiki, debug=True))
