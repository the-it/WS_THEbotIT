import os
from pathlib import Path

import pywikibot
from pywikibot import Site

from tools.bots.pi import OneTimeBot

file_description = """== batch ==
Meyers Blitz-Lexikon. Die Schnellauskunft für jedermann in Wort und Bild. Leipzig: Bibliographisches Institut AG
<br />

{{NoCommons}}

== source ==
Scan from book;

== date ==
1932

== license ==
Author died more than 70 years ago - public domain
{{PD-old}}

[[Category:Meyers Blitz-Lexikon/Ausgeschnittene Abbildungen]]"""


class UploadBlitzBot(OneTimeBot):
    def task(self):
        root_dir = Path(__file__).parent
        file_list = list(os.listdir(root_dir))
        max = len(file_list)
        for idx, file in enumerate(file_list):
            if not file.endswith(".jpg"):
                continue
            self.logger.debug(f"{idx}/{max} ... {root_dir.joinpath(file)}")
            imagepage = pywikibot.FilePage(self.wiki, file)  # normalizes filename
            imagepage.text = file_description
            imagepage.upload(str(root_dir.joinpath(file)), comment="ausgeschnittenes Bild für Blitzlexikon")
        self.logger.info("THE END")


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with UploadBlitzBot(wiki=WS_WIKI, debug=True, log_to_screen=True, log_to_wiki=False) as bot:
        bot.run()
