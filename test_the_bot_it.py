__author__ = 'eso'

import requests
import json
import pprint

if __name__ == "__main__":
    try:
        headers = {'User-Agent': 'Python-urllib/3.1'}
        response = requests.get(url="http://tools.wmflabs.org/catscan2/catscan2.php?language=de&project=wikisource&categories=Autoren&max_age=120&only_new=0&format=json&get_q=1&doit=1",
                                headers = headers, timeout=15)
        response_byte = response.content
        json_dict = json.loads(response_byte.decode("utf8"))
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(json_dict['*'][0]['a']['*'])
        pass
    except Exception as e:
        print(e)
