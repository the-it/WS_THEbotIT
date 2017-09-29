import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir + os.sep))

from pywikibot import Site
from scripts.service.re.scanner import ReScanner
from scripts.service.re.status import ReStatus
from scripts.service.gl.status import GlStatus

def run_bot(bot):
    with bot:
        bot.run()

if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    run_bot(ReStatus(wiki=wiki, debug=False))
