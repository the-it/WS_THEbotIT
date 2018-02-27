__author__ = 'erik'

import requests
import re


def add_zeros(number, digits):
    number_str = str(number)
    if number < 10:
        for members in range(digits-1):
            number_str = "0" + number_str
    elif number < 100:
        for members in range(digits-2):
            number_str = "0" + number_str
    elif number < 1000:
        for members in range(digits-3):
            number_str = "0" + number_str
    return number_str

file = open('themenseite.txt', 'w', encoding="utf-8")

for i in range(1, 224):
    try:
        response = requests.get(url="http://gdz.sub.uni-goettingen.de/dms/load/mod/?PPN=PPN266833020_"+add_zeros(i, 4),
                                headers={'User-Agent': 'Python-urllib/3.1'}, timeout=2)
        response_str = str(response.content)
        hit = re.findall(">\d{4}<", response_str)
        year = hit[2][1:5]
        print(':*{{Anker|Band'+str(i)+'}}Band '+str(i)+': '+year+' {{GDZ|266833020_'+add_zeros(i, 4)+'}}')
        #file.write('{{Vorlage:Journal für die reine und angewandte Mathematik/Eintrag|' + str(i) + '|' + year + "}}\n")
    except Exception:
        pass
file.close()
