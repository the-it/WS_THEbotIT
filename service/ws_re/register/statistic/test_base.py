from datetime import date
from unittest import mock

import pytest
from testfixtures import compare

from service.ws_re.register.statistic.base import (
    SUMMARY,
    current_state,
    history_entries,
    lemmas_per_column,
    load_volume_lemmas,
    parse_datestamp,
    render_template,
    save_json_page,
    save_page,
    state_at,
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


class TestHistory:
    def test_parse_datestamp(self):
        compare(date(2013, 3, 5), parse_datestamp("130305"))

    def test_history_entries(self):
        lemma = {"history": {"2": "120601", "0": "100101"}}
        compare([(date(2010, 1, 1), 0), (date(2012, 6, 1), 2)], history_entries(lemma))
        compare([], history_entries({}))
        compare([], history_entries({"history": None}))

    def test_state_at(self):
        history = [(date(2010, 1, 1), 0), (date(2012, 6, 1), 2), (date(2015, 1, 1), 3)]
        compare(None, state_at(history, date(2009, 12, 31)))
        compare(0, state_at(history, date(2010, 1, 1)))
        compare(2, state_at(history, date(2014, 12, 31)))
        compare(3, state_at(history, date(2020, 1, 1)))
        compare(None, state_at([], date(2020, 1, 1)))

    def test_current_state(self):
        # dropped back: the higher states were deleted, korrigiert carries the date of the drop
        compare(2, current_state({"history": {"0": "070101", "2": "071001"}}))
        compare(None, current_state({"lemma": "never created"}))


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
        text = render_template("history_table.wiki", groups="G", columns="C", rows="R")
        compare('{| class="wikitable" style="text-align:right"\n! rowspan="2" | Datum\nG\n|-\nC\nR\n|}\n', text)

    def test_missing_value_raises(self):
        with pytest.raises(KeyError):
            render_template("history_table.wiki", groups="G")


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
