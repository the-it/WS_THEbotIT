# pylint: disable=no-self-use
from unittest import TestCase

from testfixtures import compare

from service.ws_re.template.re_author import REAuthor


class TestREAuthor(TestCase):
    def test_from_template(self):
        string_template = "{{REAutor|Nagl.}}"
        author_template = REAuthor.from_template(string_template)
        compare("Nagl.", author_template.short_string)
        compare("", author_template.issue)
        compare("", author_template.full_identification)
        compare("Nagl.", author_template.identification)
        compare(string_template, str(author_template))

    def test_from_template_issue(self):
        string_template = "{{REAutor|Nagl.|IV,1}}"
        author_template = REAuthor.from_template(string_template)
        compare("Nagl.", author_template.short_string)
        compare("IV,1", author_template.issue)
        compare("", author_template.full_identification)
        compare("Nagl.", author_template.identification)
        compare(string_template, str(author_template))

    def test_from_template_full_identification(self):
        string_template = "{{REAutor|Nagl.||Albert_Nagl}}"
        author_template = REAuthor.from_template(string_template)
        compare("Nagl.", author_template.short_string)
        compare("", author_template.issue)
        compare("Albert_Nagl", author_template.full_identification)
        compare("Albert_Nagl", author_template.identification)
        compare(string_template, str(author_template))

    def test_from_template_full(self):
        string_template = "{{REAutor|Nagl.|IV,1|Albert_Nagl}}"
        author_template = REAuthor.from_template(string_template)
        compare("Nagl.", author_template.short_string)
        compare("IV,1", author_template.issue)
        compare("Albert_Nagl", author_template.full_identification)
        compare("Albert_Nagl", author_template.identification)
        compare(string_template, str(author_template))
