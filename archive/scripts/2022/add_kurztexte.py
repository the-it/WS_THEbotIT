from datetime import datetime

from pywikibot import Site

from service.ws_re.register.registers import Registers
from service.ws_re.scanner.tasks.add_short_description import KURZTask
from archive.service.pi import WikiLogger

if __name__ == "__main__":  # pragma: no cover
    wiki = Site(code="de", fam="wikisource", user="THEbotIT")
    logger = WikiLogger("", datetime.now())
    task = KURZTask(wiki, logger)
    registers = Registers()
    for volume in registers.volumes.values():
        for lemma in volume:
            if lemma.exists or lemma.short_description:
                continue
            if lemma.sort_key in task.short_description_lookup:
                lemma.update_lemma_dict(update_dict={"short_description": task.short_description_lookup[lemma.sort_key]})
    registers.persist()
