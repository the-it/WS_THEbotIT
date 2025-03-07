from unittest import TestCase

import pywikibot
from testfixtures import compare

from tools.template_expansion import TemplateExpansion
from tools.test import real_wiki_test


@real_wiki_test
class TestTemplateExpansion(TestCase):
    wiki = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")

    def test_expand_simple(self):
        input_text = """{{Textdaten
|AUTOR=[[Friedrich Schiller]]
|TITEL=Das Glück und die Weisheit
|SUBTITEL=
|HERKUNFT=[[Anthologie auf das Jahr 1782]], S. 76–77
|HERAUSGEBER=[[Friedrich Schiller]]
|AUFLAGE=
|ENTSTEHUNGSJAHR=
|ERSCHEINUNGSJAHR=1782
|ERSCHEINUNGSORT=Stuttgart
|VERLAG=J. B. Metzler
|ÜBERSETZER=
|ORIGINALTITEL=
|ORIGINALSUBTITEL=
|ORIGINALHERKUNFT=
|WIKIPEDIA=
|BILD=
|QUELLE=[[c:File:De Anthologie 1782 076.jpg|Commons]]
|KURZBESCHREIBUNG=
|SONSTIGES=
|BEARBEITUNGSSTAND=fertig
|VORIGER=Die Rache der Musen, eine Anekdote vom Helikon
|NÄCHSTER=Räzel
|INDEXSEITE=Anthologie auf das Jahr 1782
}}
{{BlockSatzStart}}
{{PoemPR|76|De Anthologie 1782 076.jpg}}
{{SeitePR|77|De Anthologie 1782 077.jpg|t1}}
{{BlockSatzEnd}}

{{SORTIERUNG:Gluck und die Weisheit #Das}}
[[Kategorie:Anthologie auf das Jahr 1782]]
[[Kategorie:Friedrich Schiller]]
[[Kategorie:Gedicht]]
[[Kategorie:1780er Jahre]]
[[Kategorie:Deutsche Philologie]]
[[Kategorie:Deutschland]]
[[Kategorie:Neuhochdeutsch]]

[[fr:La Fortune et la Sagesse]]
[[ru:С временщиком Фортуна в споре (Шиллер/Тютчев)/ПСС 2002 (СО)]]"""
        expander = TemplateExpansion(input_text, self.wiki)
        expect = """{{Textdaten
|AUTOR=[[Friedrich Schiller]]
|TITEL=Das Glück und die Weisheit
|SUBTITEL=
|HERKUNFT=[[Anthologie auf das Jahr 1782]], S. 76–77
|HERAUSGEBER=[[Friedrich Schiller]]
|AUFLAGE=
|ENTSTEHUNGSJAHR=
|ERSCHEINUNGSJAHR=1782
|ERSCHEINUNGSORT=Stuttgart
|VERLAG=J. B. Metzler
|ÜBERSETZER=
|ORIGINALTITEL=
|ORIGINALSUBTITEL=
|ORIGINALHERKUNFT=
|WIKIPEDIA=
|BILD=
|QUELLE=[[c:File:De Anthologie 1782 076.jpg|Commons]]
|KURZBESCHREIBUNG=
|SONSTIGES=
|BEARBEITUNGSSTAND=fertig
|VORIGER=Die Rache der Musen, eine Anekdote vom Helikon
|NÄCHSTER=Räzel
|INDEXSEITE=Anthologie auf das Jahr 1782
}}
{{BlockSatzStart}}
{{center|'''Das Glück und die Weisheit.'''}}


<poem>
Entzweit mit einem Favoriten,
{{idt}}Flog einst Fortun’ der Weisheit zu.
„Ich will dir meine Schäze bieten,
{{idt}}„Sei meine Freundinn du!

{{Zeile|5}}„Mein Füllhorn goß ich dem Verschwender
{{idt}}„In seinen Schoos, so mütterlich!
„Und sieh! Er fodert drum nicht minder,
{{idt}}„Und nennt noch geizig mich.

„Komm Schwester laß uns Freundschaft schliessen,
{{Zeile|10}}{{idt}}„Du keuchst so schwer an deinem Pflug.
„In deinen Schoos will ich sie giessen,
{{idt}}„Auf, folge mir! – Du hast genug.“</poem>
<poem>
Die Weisheit läßt die Schaufel sinken
{{idt}}Und wischt den Schweiß vom Angesicht.
{{Zeile|15}}„Dort eilt dein Freund – sich zu erhenken,
{{idt}}„Versöhnet euch – ich brauch dich nicht.“

{{right|Rr.}}
</poem>
{{BlockSatzEnd}}

{{SORTIERUNG:Gluck und die Weisheit #Das}}
[[Kategorie:Anthologie auf das Jahr 1782]]
[[Kategorie:Friedrich Schiller]]
[[Kategorie:Gedicht]]
[[Kategorie:1780er Jahre]]
[[Kategorie:Deutsche Philologie]]
[[Kategorie:Deutschland]]
[[Kategorie:Neuhochdeutsch]]

[[fr:La Fortune et la Sagesse]]
[[ru:С временщиком Фортуна в споре (Шиллер/Тютчев)/ПСС 2002 (СО)]]"""
        compare(expect, expander.expand())

    def test_expand_nothing_to_do(self):
        text_input = """{{Textdaten
|AUTOR=[[Friedrich Schiller]]
|TITEL=Das Glück und die Weisheit
}}
{{BlockSatzStart}}"""
        expander = TemplateExpansion(text_input, self.wiki)
        expect = """{{Textdaten
|AUTOR=[[Friedrich Schiller]]
|TITEL=Das Glück und die Weisheit
}}
{{BlockSatzStart}}"""
        compare(expect, expander.expand())

    def test_expand_bug_herder(self):
        # the target lemma for the inclusion has incomplete tags, don't handle such cases
        text_input = """{{BlockSatzStart}}
{{SeitePR|30|THEbotIT/tests/template expansion/2|B}}
{{BlockSatzEnd}}"""
        with self.assertRaises(ValueError):
            TemplateExpansion(text_input, self.wiki).expand()
