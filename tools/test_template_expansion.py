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

    def test_expand_tag(self):
        text_input = """{{BlockSatzStart}}
<pages index="Gottfried August Bürger Gedichte 1778.pdf" from=227 to=229 />
{{BlockSatzEnd}}"""
        expander = TemplateExpansion(text_input, self.wiki)
        expect = """{{BlockSatzStart}}
{{LineCenterSize|125|36|'''Abendfantasie eines Liebenden.'''}}
{{LineCenterSize|80|12|Im Frühjahr 1774.}}


<poem>{{idt}}In weiche Ruh hinabgesunken,<!-- erste Zeile -->
Ungestört von Harm und Not,
Vom süssen Labebecher trunken,
Den ihr der Gott des Schlummers bot,
{{Zeile|5}}Woleingelult vom Abendliede
Der wachen Freundin Nachtigal,
Schläft meine Herzens-Adonide
Nun ihr behäglich Schläfchen al.

{{idt}}Wolauf, mein liebender Gedanke,
{{Zeile|10}}Wolauf, zu ihrem Lager hin!
Und webe, gleich der Epheuranke,
Dich um die traute Schläferin!
Geneus der übersüssen Fülle
Von aller Erdenseligkeit,
{{Zeile|15}}Wovon zu kosten noch ihr Wille,
Und ewig ach! vielleicht verbeut! –</poem>

{{PRZU}}<poem>{{idt}}Ahi! Was hör’ ich für Gesäusel?
Das ist ihr Schlummerodemzug.
So leise wallt, durch das Gekräusel
{{Zeile|20}}Des jungen Laubes, Zefyrs Flug.
Ahi! Da hör’ ich das Gestöne,
Das Wollust aus den Busen stöst,
Wie Bienensang und Schilfgetöne,
Wann Abendwind dazwischen bläst.

{{Zeile|25}}{{idt}}O, wie so schön dahin gegossen,
Umleuchtet sie des Mondes Licht!
Die Blumen der Gesundheit sprossen
Auf ihrem wonnigen Gesicht.
Die Arme liegen ausgeschlagen,
{{Zeile|30}}Als wolten sie, mit Innigkeit,
Um den den Liebesknoten schlagen,
Dem sie im Traume ganz sich weiht. –</poem>

{{PRZU}}<poem>{{idt}}Nun kehre wieder! Nun entwanke
Dem Wonnebett’! Du hast genug!
{{Zeile|35}}Sonst wirst du trunken, mein Gedanke,
Sonst lähmt der Taumel deinen Flug.
Du loderst auf in Durstesflammen! –
Ha! wirf ins Meer der Wonne dich!
Schlagt, Wellen, über mir zusammen!
{{Zeile|40}}Ich brenne! brenne! kühlet mich!</poem>
{{BlockSatzEnd}}"""
        compare(expect, expander.expand())

    def test_expand_lst(self):
        text_input = """{{BlockSatzStart}}
{{#lst:Seite:Wünschelruthe Ein Zeitblatt 161.jpg|h1}}
{{BlockSatzEnd}}"""
        expander = TemplateExpansion(text_input, self.wiki)
        expect = """{{BlockSatzStart}}

{{Center|'''Von Clotilde de Vallon-Chalys'''}}
{{Center|(aus dem 15. Jahrhundert)}}
{{Center|''nach der Ausgabe von Vanderbourg.''}}


{{Linie}}

{{BlockSatzEnd}}"""
        compare(expect, expander.expand())
