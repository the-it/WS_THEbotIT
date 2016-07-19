__author__ = 'eso'

from tools.catscan import PetScan
import re

watch_themes = ['Allgemeines, Informations-, Buch- und Bibliothekswesen',
                'Archäologie',
                'Astronomie',
                'Bauwesen',
                'Bergbau',
                'Biologie',
                'Chemie',
                'Geografie',
                'Geowissenschaften und Karten',
                'Mathematik',
                'Medizin',
                'Physik',
                'Technik',
                'Wirtschaftswissenschaften']

def crawler_cat_index_site():
    searcher_werke  =PetScan()
    for item in watch_themes:
        searcher_werke.add_positive_category(item)
    searcher_werke.add_negative_category('Zeitschrift')
    searcher_werke.set_search_depth(4)
    searcher_werke.set_logic(log_or=True)
    list_werke = searcher_werke.run()
    for row in range(len(list_werke)):
        list_werke[row] = list_werke[row]['a']['title']
    pass
    all_sites = set([])
    counter = 1
    for werk in list_werke:
        searcher_sites = PetScan()
        searcher_sites.add_namespace('Seite')
        searcher_sites.add_positive_category('Fertig')
        searcher_sites.add_positive_category('Korrigiert')
        searcher_sites.add_positive_category('Unkorrigiert')
        searcher_sites.set_logic(log_or=True)
        searcher_sites.add_any_outlink(werk)
        # this link have a bug on catscan2
        # http://tools.wmflabs.org/catscan2/catscan2.php?project=wikisource&categories=Fertig%0D%0AKorrigiert%0D%0AUnkorrigiert&comb[union]=1&ns[102]=1&outlinks_any=Einige+Bemerkungen+%C3%BCber+die+von+Dr.+Liskovius+ver%C3%B6ffentlichten+Resultate+seiner+%E2%80%9EUntersuchungen+%C3%BCber+den+Einflu%C3%9F+der+verschiedenen+Weite+der+Labialpfeifen+auf+ihre+Tonh%C3%B6he%E2%80%9C&interface_language=de
        sites = searcher_sites.run()
        if len(sites) > 0:
            for row in range(len(sites)):
                sites[row] = sites[row]['a']['title']
            all_sites = all_sites | set(sites)
        else:
            searcher_index = PetScan()
            searcher_index.add_any_outlink(werk)
            searcher_index.add_namespace('Index')
            searcher_index.add_positive_category('Index')
            index = searcher_index.run()
            if index:
                searcher_sites = PetScan()
                searcher_sites.add_namespace('Seite')
                searcher_sites.add_positive_category('Fertig')
                searcher_sites.add_positive_category('Korrigiert')
                searcher_sites.add_positive_category('Unkorrigiert')
                searcher_sites.set_logic(log_or=True)
                searcher_sites.add_any_outlink(index[0]['a']['nstext'] + ':' + index[0]['a']['title'])
                # this link have a bug on catscan2
                # http://tools.wmflabs.org/catscan2/catscan2.php?project=wikisource&categories=Fertig%0D%0AKorrigiert%0D%0AUnkorrigiert&comb[union]=1&ns[102]=1&outlinks_any=Einige+Bemerkungen+%C3%BCber+die+von+Dr.+Liskovius+ver%C3%B6ffentlichten+Resultate+seiner+%E2%80%9EUntersuchungen+%C3%BCber+den+Einflu%C3%9F+der+verschiedenen+Weite+der+Labialpfeifen+auf+ihre+Tonh%C3%B6he%E2%80%9C&interface_language=de
                sites = searcher_sites.run()
            else:
                print(werk)
        print(counter, '/', len(list_werke), ' result:', len(all_sites))
        counter += 1
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.writelines(["Seite:%s\n" % item  for item in all_sites])

def cat_crawler():
    searcher_werke = PetScan()
    for item in watch_themes:
        searcher_werke.add_positive_category(item)
        searcher_werke.set_logic(log_or=True)
    searcher_werke.set_search_depth(4)
    list_werke = searcher_werke.run()
    for row in range(len(list_werke)):
        list_werke[row] = list_werke[row]['a']['title']
    with open('output_cat.txt', 'w', encoding='utf-8') as f:
        f.writelines(["%s\n" % item  for item in list_werke])

if __name__ == "__main__":
    crawler_cat_index_site()
