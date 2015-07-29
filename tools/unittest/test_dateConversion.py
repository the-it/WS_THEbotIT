from unittest import TestCase

__author__ = 'eso'

from tools.date_conversion import DateConversion

class TestDateConversion(TestCase):
#  def setUp(self):
#    converter = DateConversion()

  def test__chop_ref(self):
    converter = DateConversion('18. November 1856<ref>[http://www.bbf.dipf.de/cgi-opac/digiakt.pl?id=p191142 Personalbogen] bei der Bibliothek für Bildungsgeschichtliche Forschung</ref>')
    self.assertEqual('1856-11-18', str(converter))
    del converter

    converter = DateConversion('18. November 1856{{CRef||[http://www.bbf.dipf.de/cgi-opac/digiakt.pl?id=p191142 Personalbogen] bei der Bibliothek für Bildungsgeschichtliche Forschung}}')
    self.assertEqual('1856-11-18', str(converter))