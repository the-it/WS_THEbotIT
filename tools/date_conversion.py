__author__ = 'Erik Sommer'

import re

month_mapping = {"Januar": '01',
                 "Jänner": '01',
                 "Februar": '02',
                 "März": '03',
                 "April": '04',
                 "Mai": '05',
                 "Juni": '06',
                 "Juli": '07',
                 "August": '08',
                 "September": '09',
                 "Oktober": '10',
                 "November": '11',
                 "Dezember": '12',}



class DateConversion:
    """

    """
    def __init__(self, rawstring):
        self.rawstring = rawstring

    def  __str__(self):
        #chop the unused parts of the string
        str_re_form = self._chop_ref(self, self.rawstring)
        #sort for structure of the information
        if re.match('\A\d\d\.? (\d\d?|Jan|Jän|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\w* (\d{1,4})\Z', str_re_form):
            # Fall 1
            li_str = re.split(' ', str_re_form)
            li_str[0] = re.sub('\.', '', li_str[0]) # Punkt aus dem Tag entfernen
            li_str[1] = month_mapping[li_str[1]]  #Monat in Zahl verwandeln
            str_re_form = ''.join([li_str[2], '-', li_str[1], '-', li_str[0]])

        #interpret the information
        return str_re_form

    @ staticmethod
    def _chop_ref(self, rawstring):
        str_re_value = re.sub('<ref>.+</ref>', '', rawstring)
        str_re_value = re.sub('{{CRef\|.+}}', '', str_re_value)
        return str_re_value

