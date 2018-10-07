from pathlib import Path

from lxml import etree

from test import *
from tools import path_to_str


def _get_all_xml_files():
    path_to_register = Path(__file__).parent
    return ("file1.xml",)


@ddt
class TestValidateXml(TestCase):
    def _get_register_xml(self):
        path_to_xsd = Path(__file__).parent.joinpath("register.xsd")
        with open(path_to_str(path_to_xsd)) as xsd_file:
            return etree.XMLSchema(etree.parse(xsd_file))

    def setUp(self):
        self.register_xsd = self._get_register_xml()

    @idata(_get_all_xml_files())
    def test_register_xml(self, file):
        path_to_xml = Path(__file__).parent.joinpath(file)
        with open(path_to_str(path_to_xml)) as xml:
            doc_to_check = etree.parse(xml)
            self.register_xsd.assertValid(doc_to_check)
