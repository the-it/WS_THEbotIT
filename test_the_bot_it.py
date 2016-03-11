import requests
import re
import unicodedata

letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
letters = "AB"

dict_for_symbols = {}

for letter in letters:
    print(letter)
    dict_for_symbols.update({letter: []})
    dict_for_symbols.update({letter.lower(): []})
    response = requests.get(url="http://www.fileformat.info/info/unicode/char/search.htm?q={}&preview=none".format(letter), headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}, timeout=30)
    matches = re.findall('<td><a href="\d{4}\/index\.htm">([\w\s]*)<\/a><\/td>', response.text)
    for match in matches:
        try:
            unicode_letter = unicodedata.lookup(match)
            print(re.search("CAPITAL", match), match)
            if re.search("CAPITAL", match):
                print(dict_for_symbols[letter].append(unicode_letter))
                print(dict_for_symbols[letter])
                dict_for_symbols.update({letter: dict_for_symbols[letter].append(unicode_letter)})

        except:
            print("{} doesnt exist".format(match))
