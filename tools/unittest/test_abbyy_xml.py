__author__ = 'Erik Sommer'

import sys

from unittest import TestCase
from tools.abbyy_xml import AbbyyXML


class TestAbbyyXML(TestCase):
    def test_read(self):
        test_string = '<xml></xml>'
        reader = AbbyyXML(test_string)
        self.assertIs(str, type(reader.getText()))

    def test_process_char(self,):
        test_string = '<charParams l="745" t="324" r="771" b="351" wordStart="1" wordFromDictionary="1" wordNormal="1" wordNumeric="0" wordIdentifier="0" charConfidence="100" serifProbability="255" wordPenalty="0" meanStrokeWidth="36">R</charParams>'
        reader = AbbyyXML(test_string)
        self.assertEqual('R', reader.getText())

