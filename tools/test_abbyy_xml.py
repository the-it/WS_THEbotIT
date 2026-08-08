from unittest import TestCase

from tools.abbyy_xml import AbbyyXML


def _char_params(text: str) -> str:
    return "".join(f"<charParams>{char}</charParams>" for char in text)


def _line(text: str) -> str:
    return f"<line><formatting>{_char_params(text)}</formatting></line>"


def _paragraph(*lines: str) -> str:
    return "<par>" + "".join(_line(line) for line in lines) + "</par>"


def _block(*paragraphs: str) -> str:
    return "<block><text>" + "".join(paragraphs) + "</text></block>"


def _document(*blocks: str) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?><document><page>' + "".join(blocks) + "</page></document>"


class TestAbbyyXML(TestCase):
    def test_single_line(self):
        reader = AbbyyXML(_document(_block(_paragraph("abc"))))
        self.assertEqual("abc\n\n", reader.get_text())

    def test_multiple_lines_in_one_paragraph(self):
        reader = AbbyyXML(_document(_block(_paragraph("first", "second"))))
        self.assertEqual("firstsecond\n\n", reader.get_text())

    def test_multiple_paragraphs_and_blocks(self):
        reader = AbbyyXML(_document(_block(_paragraph("a"), _paragraph("b")), _block(_paragraph("c"))))
        self.assertEqual("a\nb\n\nc\n\n", reader.get_text())

    def test_only_first_page_is_processed(self):
        two_pages = (
            '<?xml version="1.0" encoding="UTF-8"?><document>'
            f"<page>{_block(_paragraph('one'))}</page>"
            f"<page>{_block(_paragraph('two'))}</page>"
            "</document>"
        )
        reader = AbbyyXML(two_pages)
        self.assertEqual("one\n\n", reader.get_text())

    def test_process_document_equals_get_text(self):
        reader = AbbyyXML(_document(_block(_paragraph("xy"))))
        self.assertEqual(reader.process_document(), reader.get_text())
