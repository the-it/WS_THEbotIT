import requests

for i in range(813, 815):
    print(i)
    picture = requests.get(url='http://bibliothek.bbaw.de/DAS_jpg/07-abh/18201821/jpg-1000/00000'
                               + str(i)
                               + '.jpg', headers={'User-Agent': 'Python-urllib/3.1'},
                           timeout=2)
    fobj = open("b_" + str(i) + ".jpg", "wb")
    fobj.write(picture.content)
    fobj.close()
