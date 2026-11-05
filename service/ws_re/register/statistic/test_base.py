from unittest import mock

import pytest
from testfixtures import compare

from service.ws_re.register.statistic.base import (
    SUMMARY,
    lemmas_per_column,
    load_volume_lemmas,
    render_template,
    save_json_page,
    save_page,
)
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from service.ws_re.volumes import Volume


def _page(exists: bool, text: str = "") -> mock.MagicMock:
    page = mock.MagicMock()
    page.exists.return_value = exists
    page.text = text
    page.title.return_value = "Title"
    return page


class TestLoadVolumeLemmas(BaseTestRegister):
    def test_skips_volumes_without_json_file(self):
        copy_tst_data("I_1_alpha", "I_1")
        present = Volume(name="I,1", year=1893, data_item="Q1")
        missing = Volume(name="II,1", year=1896, data_item="Q2")
        with mock.patch("service.ws_re.register.statistic.base.Volumes") as volumes_mock:
            volumes_mock.return_value.all_volumes = [present, missing]
            result = list(load_volume_lemmas())
        compare(1, len(result))
        compare(present, result[0][0])
        compare(True, len(result[0][1]) > 0)


class TestLemmasPerColumn:
    def test_shared_and_open_ended(self):
        lemmas = [
            {"lemma": "a", "chapters": [{"start": 1, "end": 2}]},
            {"lemma": "no chapters", "chapters": []},
            # open ended, extends up to the column before the next lemma
            {"lemma": "b", "chapters": [{"start": 2}]},
            {"lemma": "c", "chapters": [{"start": 4, "end": 4}]},
        ]
        compare([[0], [0, 2], [2], [3], []], lemmas_per_column(lemmas, 1, 5))


class TestRenderTemplate:
    def test_substitutes_placeholders(self):
        text = render_template("statistic_page.wiki", article_chart="A", column_chart="C")
        compare(True, "{{#chart:A.chart}}" in text)
        compare(True, "{{#chart:C.chart}}" in text)

    def test_missing_value_raises(self):
        with pytest.raises(KeyError):
            render_template("statistic_page.wiki")


class TestSavePage:
    def test_unchanged(self):
        page = _page(True, "text")
        save_page(page, "text", mock.Mock())
        compare(False, page.save.called)

    def test_unchanged_except_trailing_whitespace(self):
        # MediaWiki strips the trailing newline on save
        page = _page(True, "text")
        save_page(page, "text\n", mock.Mock())
        compare(False, page.save.called)

    def test_changed(self):
        page = _page(True, "old")
        save_page(page, "new", mock.Mock())
        compare("new", page.text)
        page.save.assert_called_once_with(SUMMARY, bot=True)

    def test_new(self):
        page = _page(False)
        save_page(page, "new", mock.Mock())
        compare("new", page.text)
        page.save.assert_called_once_with(SUMMARY, bot=True)


class TestSaveJsonPage:
    def test_equal_content_ignores_formatting(self):
        page = _page(True, '{"a":  1}')
        save_json_page(page, {"a": 1}, mock.Mock())
        compare(False, page.save.called)

    def test_changed(self):
        page = _page(True, "no json")
        save_json_page(page, {"a": "ä"}, mock.Mock())
        compare('{\n "a": "ä"\n}', page.text)
        page.save.assert_called_once_with(SUMMARY, bot=True)

    def test_new(self):
        page = _page(False)
        save_json_page(page, {"a": 1}, mock.Mock())
        compare(True, page.save.called)
