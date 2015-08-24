from unittest import TestCase

__author__ = 'eso'

from tools.date_conversion import DateConversion


class TestDateConversion(TestCase):
  def test_normal_date(self):
    converter = DateConversion('14.04.1850')
    self.assertEqual('1850-04-14', str(converter))
    del converter

    converter = DateConversion('14.04. 1850')
    self.assertEqual('1850-04-14', str(converter))
    del converter

    converter = DateConversion('25. Februar 1822')
    self.assertEqual('1822-02-25', str(converter))
    del converter

    converter = DateConversion('25.Februar 1822')
    self.assertEqual('1822-02-25', str(converter))
    del converter

  def test__chop_ref(self):
    converter = DateConversion('18. November 1856<ref>something</ref>')
    self.assertEqual('1856-11-18', str(converter))
    del converter

    converter = DateConversion('18. November 1856{{CRef||something}}')
    self.assertEqual('1856-11-18', str(converter))

  def test_missing_day_and_month(self):
    converter = DateConversion('November 1856')
    self.assertEqual('1856-11-00', str(converter))
    del converter

    converter = DateConversion('11. 1856')
    self.assertEqual('1856-11-00', str(converter))
    del converter

    converter = DateConversion('1856')
    self.assertEqual('1856-00-00', str(converter))
    del converter

  def test_empty_date(self):
    converter = DateConversion('')
    self.assertEqual('!-00-00', str(converter))
    del converter

  def test_unimportent_words(self):
    converter = DateConversion('nach 1856')
    self.assertEqual('1856-00-00', str(converter))
    del converter

    converter = DateConversion('um 536')
    self.assertEqual('0536-00-00', str(converter))
    del converter

    converter = DateConversion('vor 1187?')
    self.assertEqual('1187-00-00', str(converter))
    del converter

    converter = DateConversion('13. Jahrhundert (?)')
    self.assertEqual('1200-00-00', str(converter))
    del converter

    converter = DateConversion('vermutlich zwischen 260 u. 275')
    self.assertEqual('0260-00-00', str(converter))
    del converter

    converter = DateConversion('Winter 1939/40')
    self.assertEqual('1939-00-00', str(converter))
    del converter

    converter = DateConversion('18. September 1908 <!-- oder 15.? 16.? -->')
    self.assertEqual('1908-09-18', str(converter))
    del converter

  def test_append_zeros(self):
    converter = DateConversion('1')
    self.assertEqual('0001-00-00', str(converter))
    del converter

    converter = DateConversion('12')
    self.assertEqual('0012-00-00', str(converter))
    del converter

    converter = DateConversion('123')
    self.assertEqual('0123-00-00', str(converter))
    del converter

    converter = DateConversion('1234')
    self.assertEqual('1234-00-00', str(converter))
    del converter

  def test_century(self):
    converter = DateConversion('12. Jahrhundert')
    self.assertEqual('1100-00-00', str(converter))
    del converter

    converter = DateConversion('1. Jahrhundert')
    self.assertEqual('0000-00-00', str(converter))
    del converter

  def test_two_dates(self):
    converter = DateConversion('1081/1085')
    self.assertEqual('1081-00-00', str(converter))
    del converter

    converter = DateConversion('2./3. Jahrhundert')
    self.assertEqual('0200-00-00', str(converter))
    del converter

    converter = DateConversion('nach 120/119 v. Chr')
    self.assertEqual('-9879-00-00', str(converter))
    del converter

    converter = DateConversion('zwischen 475 und 480 n. Chr.')
    self.assertEqual('0475-00-00', str(converter))
    del converter

    converter = DateConversion('25. oder 26. Februar 1820')
    self.assertEqual('1820-02-26', str(converter))
    del converter

    converter = DateConversion('zwischen Oktober 1509 und Januar 1510')
    self.assertEqual('1509-10-00', str(converter))
    del converter

  def test_before_domini(self):
    converter = DateConversion('1. Jahrhundert n. Chr.')
    self.assertEqual('0000-00-00', str(converter))
    del converter

    converter = DateConversion('430 v. Chr.')
    self.assertEqual('-9569-00-00', str(converter))
    del converter

    converter = DateConversion('um 430 v. Chr.')
    self.assertEqual('-9569-00-00', str(converter))
    del converter

    converter = DateConversion('um 500 n. Chr.')
    self.assertEqual('0500-00-00', str(converter))
    del converter

    converter = DateConversion('2. Jahrhundert v. Chr.')
    self.assertEqual('-9799-00-00', str(converter))
    del converter

    converter = DateConversion('unsicher: 13. Juli 100 v. Chr.')
    self.assertEqual('-9899-07-13', str(converter))
    del converter

  def test_date_dont_known(self):
    converter = DateConversion('unbekannt')
    self.assertEqual('!-00-00', str(converter))
    del converter

    converter = DateConversion('Unbekannt')
    self.assertEqual('!-00-00', str(converter))
    del converter