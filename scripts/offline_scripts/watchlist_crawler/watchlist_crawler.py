__author__ = 'eso'

from tools.catscan import CatScan

searcher_werke  =CatScan()
searcher_werke.add_positive_category('Physik')
searcher_werke.set_depth(2)
list_werke = searcher_werke.run()
for row in range(len(list_werke)):
    list_werke[row] = list_werke[row]['a']['title']
pass
searcher_index = CatScan()
searcher_index.add_namespace('Index')
searcher_index.add_positive_category('Index')
searcher_index.add_any_outlink(list_werke[0])
index = searcher_index.run()
pass
searcher_sites = CatScan()
searcher_sites.add_namespace('Seite')
searcher_sites.add_positive_category('Fertig')
searcher_sites.add_positive_category('Korrigiert')
searcher_sites.add_positive_category('Unkorrigiert')
searcher_sites.set_logic(log_or=True)
searcher_sites.add_any_outlink('Index:'+index[0]['a']['title'])
sites = searcher_sites.run()
pass