__author__ = 'eso'

from tools.catscan import CatScan
import re

def crawler():
    searcher_werke  =CatScan()
    searcher_werke.add_positive_category('Physik')
    searcher_werke.set_depth(2)
    list_werke = searcher_werke.run()
    for row in range(len(list_werke)):
        list_werke[row] = list_werke[row]['a']['title']
    pass
    all_sites = set([])
    counter = 1
    for werk in list_werke:
        searcher_sites = CatScan()
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
            print(werk)
        print(counter, len(all_sites))
        counter += 1
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.writelines(["Seite:%s\n" % item  for item in all_sites])

def clean_output():
    with open('output.txt', 'r', encoding='utf-8') as input:
        sites = input.read().splitlines()
        filtered_sites = set([])
        for site in sites:
            if not re.match('.*Gartenlaube.*', site):
                filtered_sites.add(site)
    with open('output_filter.txt', 'w', encoding='utf-8') as f:
        f.writelines(["Seite:%s\n" % item  for item in filtered_sites])


if __name__ == "__main__":
    crawler()