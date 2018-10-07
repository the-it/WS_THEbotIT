from os import listdir
from pathlib import Path
from io import StringIO

from lxml import etree
import requests

from test import *
from tools import path_to_str


def _get_all_xml_files():
    path_to_register = Path(__file__).parent
    list_of_files = [x for x in listdir(path_to_str(path_to_register)) if x.split(".")[-1] == "xml"]
    return list_of_files


@ddt
class TestValidateXml(TestCase):
    path_to_xsd = Path(__file__).parent.joinpath("register.xsd")

    @classmethod
    def _get_register_xml(cls):
        with open(path_to_str(cls.path_to_xsd)) as xsd_file:
            return etree.XMLSchema(etree.parse(xsd_file))

    @classmethod
    def setUpClass(cls):
        cls.register_xsd = cls._get_register_xml()

    @idata(_get_all_xml_files())
    def test_register_xml(self, file):
        path_to_xml = Path(__file__).parent.joinpath(file)
        with open(path_to_str(path_to_xml)) as xml:
            doc_to_check = etree.parse(xml)
            self.register_xsd.assertValid(doc_to_check)

    @skip("Takes way too much time.")
    def test_check_xsd(self):
        r = requests.get('https://www.w3.org/2009/XMLSchema/XMLSchema.xsd')
        xsd_for_xsd = StringIO(r.text)
        xsd_schema = etree.XMLSchema(etree.parse(xsd_for_xsd))
        with open(path_to_str(self.path_to_xsd)) as register_xsd:
            xsd_schema.assertValid(etree.parse(register_xsd))
