__author__ = 'eso'

import requests
import re

for i in range(12, 70, 2):
    print(i)
    if i < 100:
        number = '0'+str(i)
    else:
        number = str(i)
    response = requests.get(url="https://commons.wikimedia.org/wiki/File:OrbisPictus_b_"+number+".jpg",
                            headers={'User-Agent': 'Python-urllib/3.1'}, timeout=2)
    print(response.content)
    finding = re.findall('<a href="https://upload.wikimedia.org/wikipedia/commons/\w/\w\w/OrbisPictus_b_\d\d\d.jpg" class="internal" title="OrbisPictus b \d\d\d.jpg">Original file</a>', str(response.content))
    url_origin = re.findall('https://upload.wikimedia.org/wikipedia/commons/\w/\w\w/OrbisPictus_b_\d\d\d.jpg', finding[0])
    picture = requests.get(url=url_origin[0], headers={'User-Agent': 'Python-urllib/3.1'}, timeout=2)
    fobj = open("OrbisPictus_b_"+number+".jpg", "wb")
    fobj.write(picture.content)
    fobj.close()
