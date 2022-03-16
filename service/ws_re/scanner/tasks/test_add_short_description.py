from testfixtures import compare

from service.ws_re.scanner.tasks.add_short_description import KURZTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

class TestKURZTaskProcessSource(TaskTestCase):
    def test_load_short_descriptions_from_text(self):
        source_short_text = """{|class="wikitable"
|-
!Artikel!!Kurzbeschreibung
|-
|[[RE:Aachen]]||deutsche Stadt = Aquae
|-
|[[RE:Aal]]||Zoologisch
|-
|[[RE:No real description]]||(-)
|}"""
        short_text_lookup = KURZTask._load_source_short_description(source_short_text)
        compare(short_text_lookup, {"Aachen": "deutsche Stadt = Aquae", "Aal": "Zoologisch"})
