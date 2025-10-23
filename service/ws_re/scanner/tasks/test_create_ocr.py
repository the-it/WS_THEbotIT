from datetime import datetime
from pathlib import Path

from ddt import ddt, file_data
from testfixtures import compare

from service.ws_re.scanner.tasks.create_ocr import COCRTask, NoRawOCRFound
from service.ws_re.template.re_page import RePage
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger
from tools.bots.test_base import TestCloudBase
from tools.test import PageMock

OCR_BUCKET_NAME = "wiki-bots-re-ocr-prd"


@ddt
class TestCOCRTask(TestCloudBase):
    PATH_TEST_FILES = Path(__file__).parent.joinpath("test_data").joinpath("create_ocr")

    def setUp(self):
        self.page_mock = PageMock()
        self.logger = WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1),
                                 log_to_screen=False)
        self.task = COCRTask(None, self.logger)

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.s3.create_bucket(Bucket=OCR_BUCKET_NAME)

    def put_page_to_cloud(self, page_name: str):
        with open(file=self.PATH_TEST_FILES.joinpath(page_name + ".txt"), mode="r", encoding="utf-8") as file:
            self.s3_client.put_object(Bucket=OCR_BUCKET_NAME, Key=page_name + ".txt", Body=file.read().encode("utf-8"))

    def test_read_from_cloud(self):
        self.put_page_to_cloud("I A,1_0127")
        compare(2, self.task.get_raw_page("I A,1_0127").count("== RE:Ragando =="))

    def test_read_from_cloud_page_not_there(self):
        self.put_page_to_cloud("I A,1_0127")
        with self.assertRaises(NoRawOCRFound):
            self.task.get_raw_page("something_wrong")

    def test_get_full_text_of_page(self):
        self.put_page_to_cloud("I A,1_0127")
        text = self.task._get_text_for_section("I A,1", 127, start=False, end=False)
        self.assertTrue(text.startswith("\ufeff127 {{Polytonisch|sup€λsupΡάγαεα}}"))
        self.assertTrue(text.endswith("CIE 109f. 163. 1228ff.), sowie den aus dem"))

    @file_data("test_data/create_ocr/test_get_texts.yml")
    def test_get_text_start_end(self, given, expect):
        self.put_page_to_cloud(f"{given["issue"]}_{str(given["page"]).zfill(4)}")
        page_mock = PageMock()
        page_mock.title_str = f"RE:{given['title']}"
        page_mock.text = "{{REDaten}}{{REAutor|OFF}}"
        self.task.re_page = RePage(page_mock)
        text = self.task._get_text_for_section(given["issue"], given["page"], start=given["start"], end=given["end"])
        compare(expect.strip(), text)

    @file_data("test_data/create_ocr/test_detect_empty.yml")
    def test_detect_empty_content(self, given, expect):
        compare(expect, self.task._detect_empty_content(given))

    @file_data("test_data/create_ocr/test_get_text_for_article.yml")
    def test_get_text_for_article_single_page(self, given, expect):
        # Arrange: upload OCR page and set page/lemma from fixture
        self.put_page_to_cloud(f"{given['issue']}_{str(given['start_page']).zfill(4)}")
        page_mock = PageMock()
        page_mock.title_str = f"RE:{given['title']}"
        page_mock.text = "{{REDaten}}{{REAutor|OFF}}"
        self.task.re_page = RePage(page_mock)
        # Create a placeholder article with single page range
        article = Article()
        article["BAND"].value = given['issue']
        article["SPALTE_START"].value = str(given['start_page'])
        article["SPALTE_END"].value = str(given['end_page'])

        # Act
        text = self.task._get_text_for_article(article)

        # Assert
        compare(expect.strip(), text)
