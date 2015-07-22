__author__ = 'erik'

import requests
import re

file = open('themenseite.txt', 'w', encoding="utf-8")
for i in range(121, 494, 1):
    try:
        response = requests.get(url="http://gdz.sub.uni-goettingen.de/dms/load/mod/?PPN=PPN243919689_0"+str(i),
                                headers={'User-Agent': 'Python-urllib/3.1'}, timeout=2)
        response_str = str(response.content)
        hit = re.findall(">19\d{2}<",response_str)
        year = hit[0][1:5]
        print('{{Vorlage:Journal für die reine und angewandte Mathematik/Eintrag|' + str(i) + '|' + year + "}}")
        file.write('{{Vorlage:Journal für die reine und angewandte Mathematik/Eintrag|' + str(i) + '|' + year + "}}\n")
    except:
        pass