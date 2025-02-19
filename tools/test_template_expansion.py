from unittest import TestCase

import pywikibot
from testfixtures import compare

from tools.template_expansion import TemplateExpansion


class TestTemplateExpansion(TestCase):
    wiki = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")

    def test_expand_simple(self):
        input = """{{Textdaten
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
        expander = TemplateExpansion(input, self.wiki)
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
