"""
This is a little helper_script, which updates the matching wikidata data items to the page of the volume categories.
"""
import json
from pathlib import Path

import pywikibot

WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")

with open(Path(__file__).parent.joinpath("volumes.json"), "r", encoding="utf-8") as json_file:
    raw_volumes_dict = json.loads(json_file.read())
for idx, volume in enumerate(raw_volumes_dict):
    page: pywikibot.Page = pywikibot.Page(WS_WIKI, f"Kategorie:RE:Band {volume['name']}")
    item: pywikibot.ItemPage = page.data_item()
    print(volume, item.id)
    raw_volumes_dict[idx]["data_item"] = item.id
with open(Path(__file__).parent.joinpath("volumes.json"), "w", encoding="utf-8") as json_file:
    json.dump(raw_volumes_dict, json_file, indent=2)
