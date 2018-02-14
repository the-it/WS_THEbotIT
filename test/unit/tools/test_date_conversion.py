from test import *
from tools.date_conversion import DateConversion


class TestDateConversion(TestCase):
    def assert_for_equal(self, input_str:str, output_str:str):
        converter = DateConversion(input_str)
        self.assertEqual(output_str, str(converter))

    def test_normal_date(self):
        self.assert_for_equal('14.04.1850', '1850-04-14')
        self.assert_for_equal('14.04. 1850', '1850-04-14')
        self.assert_for_equal('25. Februar 1822', '1822-02-25')
        self.assert_for_equal('25.Februar 1822', '1822-02-25')

    def test__chop_ref(self):
        self.assert_for_equal('18. November 1856<ref>something</ref>', '1856-11-18')
        self.assert_for_equal('18. November 1856{{CRef||something}}', '1856-11-18')

    def test_missing_day_and_month(self):
        self.assert_for_equal('November 1856', '1856-11-00')
        self.assert_for_equal('11. 1856', '1856-11-00')
        self.assert_for_equal('1856', '1856-00-00')

    def test_empty_date(self):
        self.assert_for_equal('', '!-00-00')

    def test_unimportent_words(self):
        self.assert_for_equal('nach 1856', '1856-00-00')
        self.assert_for_equal('um 536', '0536-00-00')
        self.assert_for_equal('vor 1187?', '1187-00-00')
        self.assert_for_equal('13. Jahrhundert (?)', '1200-00-00')
        self.assert_for_equal('vermutlich zwischen 260 u. 275', '0260-00-00')
        self.assert_for_equal('Winter 1939/40', '1939-00-00')
        self.assert_for_equal('18. September 1908 <!-- oder 15.? 16.? -->', '1908-09-18')

    def test_append_zeros(self):
        self.assert_for_equal('1', '0001-00-00')
        self.assert_for_equal('12', '0012-00-00')
        self.assert_for_equal('123', '0123-00-00')
        self.assert_for_equal('1234', '1234-00-00')

    def test_century(self):
        self.assert_for_equal('12. Jahrhundert', '1100-00-00')
        self.assert_for_equal('lebte im 4. Jh. v. Chr.', '-9599-00-00')
        self.assert_for_equal('1. Jahrhundert', '0000-00-00')

    def test_two_dates(self):
        self.assert_for_equal('1081/1085', '1081-00-00')
        self.assert_for_equal('2./3. Jahrhundert', '0200-00-00')
        self.assert_for_equal('nach 120/119 v. Chr', '-9879-00-00')
        self.assert_for_equal('zwischen 475 und 480 n. Chr.', '0475-00-00')
        self.assert_for_equal('25. oder 26. Februar 1820', '1820-02-26')
        self.assert_for_equal('zwischen Oktober 1509 und Januar 1510', '1509-10-00')

    def test_before_domini(self):
        self.assert_for_equal('1. Jahrhundert n. Chr.', '0000-00-00')
        self.assert_for_equal('430 v. Chr.', '-9569-00-00')
        self.assert_for_equal('um 430 v. Chr.', '-9569-00-00')
        self.assert_for_equal('um 500 n. Chr.', '0500-00-00')
        self.assert_for_equal('2. Jahrhundert v. Chr.', '-9799-00-00')
        self.assert_for_equal('unsicher: 13. Juli 100 v. Chr.', '-9899-07-13')

    def test_date_dont_known(self):
        self.assert_for_equal('unbekannt', '!-00-00')
        self.assert_for_equal('Unbekannt', '!-00-00')
        self.assert_for_equal('?', '!-00-00')
        self.assert_for_equal('unbekannt (getauft 25. Dezember 1616)', '1616-12-25')

    def test_authorlist(self):
        self.assert_for_equal('20. Nov. 1815', '1815-11-20')

    def test_preset_for_date(self):
        self.assert_for_equal('Mitte 15. Jh.<!--1450-00-00-->', '1450-00-00')
