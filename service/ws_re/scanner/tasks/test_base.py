# pylint: disable=protected-access
from ddt import ddt, file_data
from testfixtures import compare

from service.ws_re.scanner.tasks.base import get_redirect
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


@ddt
class TestGetRedirect(TaskTestCase):
    @file_data("test_data/register_scanner/test_get_redirect.yml")
    def test_get_redirect(self, text, result):
        self.page_mock.text = text
        article = RePage(self.page_mock).first_article
        compare(result, get_redirect(article))
