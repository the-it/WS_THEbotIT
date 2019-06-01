from unittest import TestCase

from testfixtures import compare

from scripts.service.ws_re.template import ReDatenException, ARTICLE_TEMPLATE
from scripts.service.ws_re.template.article import Article


class TestReArticle(TestCase):
    def setUp(self):
        self.article = Article()

    def test_article_type(self):
        self.assertEqual(self.article.article_type, "REDaten")
        self.article.article_type = "REAbschnitt"
        self.assertEqual(self.article.article_type, "REAbschnitt")
        article = Article(article_type="REAbschnitt")
        self.assertEqual(article.article_type, "REAbschnitt")

    def test_wrong_article_type(self):
        with self.assertRaisesRegex(ReDatenException, "ReStuff is not a permitted article type."):
            Article(article_type="ReStuff")

    def test_set_text(self):
        self.assertEqual(self.article.text, "")
        self.article.text = "bla"
        self.assertEqual(self.article.text, "bla")
        article = Article(text="blub")
        self.assertEqual(article.text, "blub")

    def test_wrong_type_text(self):
        with self.assertRaisesRegex(ReDatenException, "Property text must be a string."):
            Article(text=1)

    def test_set_author(self):
        self.assertEqual(self.article.author, ("", ""))
        self.article.author = "bla"
        self.assertEqual(self.article.author, ("bla", ""))
        article = Article(author=("blub", "II,2"))
        self.assertEqual(article.author, ("blub", "II,2"))

    def test_wrong_type_author(self):
        with self.assertRaises(ReDatenException):
            Article(author=1)

    def test_properties_access(self):
        self.assertFalse(self.article["NACHTRAG"].value)
        self.article["NACHTRAG"].value = True
        self.assertTrue(self.article["NACHTRAG"].value)
        with self.assertRaises(KeyError):
            self.article["SomeShit"].value = ""

    def test_properties_iterate(self):
        iterator = iter(self.article)
        self.assertEqual(next(iterator).name, "BAND")
        self.assertEqual(next(iterator).name, "SPALTE_START")
        self.assertEqual(next(iterator).name, "SPALTE_END")
        for i in range(5):
            next(iterator)
        self.assertEqual(next(iterator).name, "WIKISOURCE")
        for i in range(6):
            next(iterator)
        self.assertEqual(next(iterator).name, "NACHTRAG")
        self.assertEqual(next(iterator).name, "ÜBERSCHRIFT")
        self.assertEqual(next(iterator).name, "VERWEIS")
        self.assertEqual(len(self.article), 18)

    def test_properties_init(self):
        article = Article(re_daten_properties={"BAND": "I 1", "NACHTRAG": True})
        self.assertEqual(article["BAND"].value_to_string(), "I 1")
        self.assertEqual(article["NACHTRAG"].value_to_string(), "ON")

    def test_properties_exception(self):
        with self.assertRaises(ReDatenException):
            Article(re_daten_properties={"BAND": 1})

    def test_simple_article(self):
        article_text = "{{REDaten}}text{{REAutor|Autor.}}"
        article = Article.from_text(article_text)
        self.assertEqual("text", article.text)

    def test_simple_article_with_whitespaces(self):
        article_text = "{{REDaten}}\n\n\t   text\t   {{REAutor|Autor.}}"
        article = Article.from_text(article_text)
        self.assertEqual("text", article.text)

    def test_from_text(self):
        article_text = "{{REDaten\n|BAND=III\n|SPALTE_START=1\n}}\ntext\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
        self.assertEqual(article.author, ("Some Author.", ""))
        self.assertEqual(article.text, "text")
        self.assertEqual(article.article_type, "REDaten")
        self.assertEqual(article["BAND"].value, "III")
        self.assertEqual(article["SPALTE_START"].value, "1")

    def test_from_text_wrong_keywords(self):
        article_text = "{{REDaten|WHATEVER=I}}" \
                       "\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "REDaten has wrong key word. --> {.*?}"):
            Article.from_text(article_text)

    def test_from_text_short_keywords(self):
        article_text = "{{REDaten|BD=I|SS=1|SE=2|VG=A|NF=B|SRT=TADA|KOR=fertig|WS=BLUB|WP=BLAB" \
                       "|XS={{START}}|XE={{END}}|GND=1234|KSCH=OFF|TJ=1949|ÜB=ON|VW=OFF|NT=ON}}" \
                       "\ntext\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
        self.assertEqual("I", article["BAND"].value)
        self.assertEqual("1", article["SPALTE_START"].value)
        self.assertEqual("2", article["SPALTE_END"].value)
        self.assertEqual("A", article["VORGÄNGER"].value)
        self.assertEqual("B", article["NACHFOLGER"].value)
        self.assertEqual("TADA", article["SORTIERUNG"].value)
        self.assertEqual("fertig", article["KORREKTURSTAND"].value)
        self.assertEqual("BLUB", article["WIKISOURCE"].value)
        self.assertEqual("BLAB", article["WIKIPEDIA"].value)
        self.assertEqual("{{START}}", article["EXTSCAN_START"].value)
        self.assertEqual("{{END}}", article["EXTSCAN_END"].value)
        self.assertEqual("1234", article["GND"].value)
        self.assertEqual("1949", article["TODESJAHR"].value)
        self.assertFalse(article["KEINE_SCHÖPFUNGSHÖHE"].value)
        self.assertTrue(article["ÜBERSCHRIFT"].value)
        self.assertFalse(article["VERWEIS"].value)
        self.assertTrue(article["NACHTRAG"].value)

    def test_from_text_wrong_property_in_REDaten(self):
        article_text = "{{REDaten\n|III\n|SPALTE_START=1\n}}\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "REDaten has property without a key word. --> {.*?}"):
            Article.from_text(article_text)

    def test_from_text_two_REDaten_templates(self):
        article_text = "{{REDaten}}{{REDaten}}\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one start template"):
            Article.from_text(article_text)

    def test_from_text_no_REDaten_templates(self):
        article_text = "\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one start template"):
            Article.from_text(article_text)

    def test_from_text_two_REAuthor_templates(self):
        article_text = "{{REDaten}}\ntext\n{{REAutor|Some Author.}}{{REAutor}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one stop template"):
            Article.from_text(article_text)

    def test_from_text_no_REAuthor_templates(self):
        article_text = "{{REDaten}}\ntext\n"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one stop template"):
            Article.from_text(article_text)

    def test_from_text_wrong_order_of_templates(self):
        article_text = "{{REAutor}}{{REDaten}}\ntext"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. Wrong order of templates."):
            Article.from_text(article_text)

    def test_complete_article(self):
        article_text = ARTICLE_TEMPLATE
        Article.from_text(article_text)

    def test_from_text_REAbschnitt(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
        self.assertEqual(article.article_type, "REAbschnitt")

    def test_from_text_text_in_front_of_article(self):
        article_text = "text{{REDaten}}text{{REAutor}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. "
                                    "There is text in front of the article."):
            Article.from_text(article_text)

    def test_from_text_text_after_article(self):
        article_text = "{{REDaten}}text{{REAutor}}text"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. "
                                    "There is text after the article."):
            Article.from_text(article_text)

    def test_to_text_simple(self):
        self.article.author = "Autor."
        self.article.text = "text"
        self.assertEqual(ARTICLE_TEMPLATE, self.article.to_text())

    def test_to_text_REAbschnitt(self):
        text = """{{REAbschnitt}}
text
{{REAutor|Autor.}}"""
        self.article.author = "Autor."
        self.article.text = "text"
        self.article.article_type = "REAbschnitt"
        self.assertEqual(text, self.article.to_text())

    def test_to_text_changed_properties(self):
        text = ARTICLE_TEMPLATE.replace("BAND=", "BAND=II")\
                               .replace("SPALTE_START=", "SPALTE_START=1000")\
                               .replace("WIKIPEDIA=", "WIKIPEDIA=Test")
        self.article.text = "text"
        self.article.author = "Autor."
        self.article["BAND"].value = "II"
        self.article["SPALTE_START"].value = "1000"
        self.article["WIKIPEDIA"].value = "Test"
        self.assertEqual(text, self.article.to_text())

    def test_hash(self):
        pre_hash = hash(self.article)
        self.article["BAND"].value = "II"
        self.assertNotEqual(pre_hash, hash(self.article))
        pre_hash = hash(self.article)
        self.article["SPALTE_START"].value = "1000"
        self.assertNotEqual(pre_hash, hash(self.article))

    def test_bug_1(self):
        test_string = """{{REDaten
|BAND=IV,1
|SPALTE_START=610
|SPALTE_END=OFF
|VORGÄNGER=Cominius 23
|NACHFOLGER=Cominius 25
|SORTIERUNG=
|KORREKTURSTAND=Platzhalter
|KSCH=OFF
|TJ=1950
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START={{REIA|IV,1|607}}
|EXTSCAN_END=
|VW=
}} 
'''24)''' ''L. Cominius Vipsanius Salutaris, domo Roma, subproc(urator) ludi magni, proc(urator) alimentor(um) per Apuliam Calabriam Lucaniam Bruttios, proc. prov(inciae) Sicil(iae), proc. capiend(orum) vec(tigalium) (?), proc. prov. Baet(icae), a cognitionib(us) domini n(ostri) Imp(eratoris) etc. etc. <!-- L. Septimi Severi Pertinac(is) Augusti, p(erfectissimus) v(ir), optimus vir et integrissimus'', CIL II 1085 = [[Hermann Dessau|{{SperrSchrift|Dessau}}]] 1406 (Ilipa); die Ehrung durch einen Untergebenen in der Baetica erfolgte bei seinem Abgang aus der Provinz, als er zu den Cognitiones des Kaisers berufen wurde. Die ''Cominia L. fil. Vipsania Dignitas c(larissima)f(emina)'', CIL IX 2336, könnte seine Tochter sein. -->

{{REAutor|Stein.}}"""
        Article.from_text(test_string)

    def test_bug_2(self):
        test_string = """{{REDaten
|BAND=XIV,1
|SPALTE_START=46
|SPALTE_END=
|VORGÄNGER=Lysippe 7
|NACHFOLGER=Lysippos 2
|SORTIERUNG=
|KORREKTURSTAND=unkorrigiert
|KSCH=on
|TJ=1962
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START={{REWL|XIV,1|45}}
|EXTSCAN_END=
|GND=
}}
'''Lysippos. 1)''' Spartaner, führt unter König Agis und als sein Nachfolger Truppen gegen Elis (400/399): Xen. hell. IH 2 29f.
{{REAutor|Kahrstedt.}}"""
        Article.from_text(test_string)

    def test_correct_case(self):
        article_text = "{{REDaten\n|Nachtrag=OFF|Ksch=OFF\n}}\ntext\n{{REAutor|Autor.}}"
        article = Article.from_text(article_text)
        self.assertEqual(ARTICLE_TEMPLATE, article.to_text())

    def test_bug_dot_added_to_author(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|S.A.†}}"
        article = Article.from_text(article_text)
        self.assertIn("{{REAutor|S.A.†}}", article.to_text())

    def test_bug_issue_number_deleted_from_author(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.|I,1}}"
        article = Article.from_text(article_text)
        compare("I,1", article.author[1])
        self.assertIn("{{REAutor|Some Author.|I,1}}", article.to_text())

    def test_bug_issue_OFF_deleted_from_author(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|OFF}}"
        article = Article.from_text(article_text)
        self.assertIn("{{REAutor|OFF}}", article.to_text())

    def test_bug_issue_OFF_deleted_from_author_no_OFF(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|A. Author.}}"
        article = Article.from_text(article_text)
        self.assertIn("{{REAutor|A. Author.}}", article.to_text())
