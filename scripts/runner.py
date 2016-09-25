import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep)

from pywikibot import Site
from scripts.service_scripts.ACTIVE_author_list import AuthorList
from scripts.service_scripts.ACTIVE_re_status import ReStatus
from scripts.service_scripts.ACTIVE_gl_status import GlStatus
from scripts.service_scripts.ACTIVE_gl_create_magazine import GlCreateMagazine
from tools.bots import SaveExecution

def run_bot(bot):
    with SaveExecution(bot):
        bot.run()

if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')

    daily_list = [AuthorList]

    weekly_list = [[],#monday
                   [],
                   [],
                   [],
                   [],
                   [GlCreateMagazine],
                   [ReStatus]]#sunday

    monthly_list = [[GlStatus]]

    #daily tasks
    for bot in daily_list:
        run_bot(bot(wiki=wiki, debug=False))

    # weekly tasks
    for bot in weekly_list[datetime.now().weekday()]:
        run_bot(bot(wiki=wiki, debug=False))

    # monthly tasks
    try:
        for bot in monthly_list[datetime.now().day]:
            run_bot(bot(wiki=wiki, debug=False))
    except IndexError:
        pass

#todo: dynamic import
#files_in_dir = os.listdir('service_scripts')
#active_files = []
#for files in files_in_dir:
#    if regex_active.search(files):
#        active_files.append(files.replace('ACTIVE_', '').replace('.py', ''))
#for file in active_files:
#    word_list = file.split('_')
#    word_list = [x.capitalize() for x in word_list]
#    class_name = ''.join(word_list)
#    __import__('scripts.service_scripts.ACTIVE_{}'.format(file), globals(), locals(), class_name, 0)
#wiki = Site(code='de', fam='wikisource', user='THEbotIT')
#run_bot(AuthorList(wiki=wiki, debug=True))

