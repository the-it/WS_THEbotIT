__author__ = 'eso'

from unittest import TestCase
from scripts.sort_filter.sort_filter import SortFilter

class TestSortFilter(TestCase):
    def setUp(self):
      self.sort_filter = SortFilter()

    def test_filter_special_cases(self):
      raw_list = [{'a': {'title': 'Die_Gartenlaube_(1877)'}},
                  {'a': {'title': 'Bestättigung_der_traurigen_Geschichte_des_P._Anians,_nebst_der_Kerkergeschichte_des_P._Mansuet_Oehningers,_Capuciners_zu_Wirzburg'}},
                  {'a': {'title': 'Der_Bock_von_Bockau_(Ziehnert)'}},
                  {'a': {'title': 'Die_Amme_zu_Hirschstein_(Ziehnert)'}},
                  {'a': {'title': 'Die_Kirche_des_ehemaligen_Cistercienser_Nonnenklosters_Porta_Coeli_zu_Tišnowic'}},
                  {'a': {'title': 'Ein_Apostel_der_Volksaufklärung'}},
                  {'a': {'title': 'Ein_Hort_des_evangelischen_Kirchengesanges'}},
                  {'a': {'title': 'Fritz_von_der_Kerkhove_(Die_Gartenlaube_1877/44)'}}]
      filtered_list = ['Bestättigung_der_traurigen_Geschichte_des_P._Anians,_nebst_der_Kerkergeschichte_des_P._Mansuet_Oehningers,_Capuciners_zu_Wirzburg',
                       'Die_Kirche_des_ehemaligen_Cistercienser_Nonnenklosters_Porta_Coeli_zu_Tišnowic',
                       'Ein_Apostel_der_Volksaufklärung']
      result = self.sort_filter.filter(raw_list)
      self.assertEqual(filtered_list, result)
