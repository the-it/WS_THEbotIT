from datetime import datetime
from pathlib import Path

from botocore import exceptions
from testfixtures import compare

from service.ws_re.scanner.tasks.create_ocr import COCRTask
from tools.bots.logger import WikiLogger
from tools.bots.test_base import TestCloudBase
from tools.test import PageMock

OCR_BUCKET_NAME = "wiki-bots-re-ocr-prd"


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
        self.task.get_raw_page("something_wrong")
        # SOLVE THIS
        # with self.assertRaises(exceptions.):
        #     self.task.get_raw_page("something_wrong")

    def test_get_full_text_of_page(self):
        self.put_page_to_cloud("I A,1_0127")
        text = self.task._get_text_for_section("I A,1", 127, start=False, end=False)
        self.assertTrue(text.startswith("\ufeff127 {{Polytonisch|sup€λsupΡάγαεα}}"))
        self.assertTrue(text.endswith("CIE 109f. 163. 1228ff.), sowie den aus dem"))
