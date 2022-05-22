import os
import re
from contextlib import suppress
from datetime import datetime
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
        root_dir = Path.home().joinpath("Dropbox/blitzlexikon")
        date_folder = root_dir.joinpath(datetime.now().strftime("%y%m%d"))
        with suppress(FileExistsError):
            os.makedirs(date_folder)

        file_list: list[str] = sorted(list(os.listdir(str(root_dir))))
        max = len(file_list)
        for idx, file in enumerate(file_list):
            if not re.match(r"LA2-Blitz-\d{4}_.+?\.jpg", file):
                continue
            self.logger.debug(f"{idx}/{max} ... {root_dir.joinpath(file)}")
            imagepage = pywikibot.FilePage(self.wiki, file)  # normalizes filename
            imagepage.text = file_description
            success = imagepage.upload(str(root_dir.joinpath(file)), comment="ausgeschnittenes Bild für Blitzlexikon")
            if success:
                os.rename(root_dir.joinpath(file), date_folder.joinpath(file))
        self.logger.info("THE END")


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with UploadBlitzBot(wiki=WS_WIKI, debug=True, log_to_screen=True, log_to_wiki=False) as bot:
        bot.run()
