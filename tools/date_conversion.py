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
                 "Dezember": '12',
                 "Jan": '01',
                 "Feb": '02',
                 "Mär": '03',
                 "Apr": '04',
                 "Jun": '06',
                 "Jul": '07',
                 "Aug": '08',
                 "Sept": '09',
                 "Okt": '10',
                 "Nov": '11',
                 "Dez": '12',
                 "1.": '01',
                 "2.": '02',
                 "3.": '03',
                 "4.": '04',
                 "5.": '05',
                 "6.": '06',
                 "7.": '07',
                 "8.": '08',
                 "9.": '09',
                 "10.": '10',
                 "11.": '11',
                 "12.": '12'}


class DateConversion:
    """

    """

    def __init__(self, rawstring):
        self.rawstring = rawstring

    def __str__(self):
        # chop the unused parts of the string
        str_re_form = self._chop_ref(self.rawstring)

        # inspect the string
        match_dont_known = re.search('(unbekannt|Unbekannt|\?)', str_re_form)
        match_preset = re.search('<!--(\d{4}-\d{2}-\d{2})-->', str_re_form)
        match_before_domino = re.search('v. Chr', str_re_form)
        match_only_century = re.search('\d{1,2}\. (Jahrhundert|Jh.)', str_re_form)
        match_complete_date = re.search('\d{1,2}(\.|\. | )'
                                        '(\d\d?|Jan|Jän|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)'
                                        '\w*(\.|\. | )(\d{1,4})', str_re_form)
        match_no_day = re.search('(\d{1,2}\.|Jan|Jän|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez)'
                                 '\w*(\.|\. | )(\d{1,4})', str_re_form)
        match_only_year = re.search('\d{1,4}', str_re_form)

        # sort for structure of the information and interpred it
        if match_preset:
            str_re_form = match_preset.group(1)
        elif match_only_century:
            # Case: only a century given
            century = re.search('\d{1,2}', match_only_century.group())
            if match_before_domino:
                century = int(century.group())
            else:
                century = int(century.group()) - 1
            year = self._append_zeros_to_year(str(century) + '00')
            str_re_form = ''.join([year, '-', '00', '-', '00'])
            del year
        elif match_complete_date:
            # Case: complete date
            li_str = re.split('[\. ]{1,2}', match_complete_date.group())
            li_str[0] = self._day_to_int(re.sub('\.', '', li_str[0]))  # Punkt aus dem Tag entfernen
            li_str[1] = self._month_to_int(li_str[1])  # Monat in Zahl verwandeln
            li_str[2] = self._append_zeros_to_year(li_str[2])  # append zeros to the year
            str_re_form = ''.join([li_str[2], '-', li_str[1], '-', li_str[0]])
        elif match_no_day:
            # Case: only month and year
            li_str = re.split(' ', match_no_day.group())
            li_str[0] = self._month_to_int(li_str[0])  # Monat in Zahl verwandeln
            li_str[1] = self._append_zeros_to_year(li_str[1])  # append zeros to the year
            str_re_form = ''.join([li_str[1], '-', li_str[0], '-', '00'])
        elif match_only_year:
            # Case: only year
            li_str = re.split(' ', match_only_year.group())
            li_str[0] = self._append_zeros_to_year(li_str[0])  # append zeros to the year
            str_re_form = ''.join([li_str[0], '-', '00', '-', '00'])
        elif str_re_form == '' or match_dont_known:
            # Case: empty rawstring
            str_re_form = '!-00-00'
        else:
            raise ValueError(str_re_form)

        # interpret the information of v. Chr.
        if match_before_domino:
            year = int(str_re_form[0:4])
            converted_year = 9999 - year
            str_re_form = '-' + self._append_zeros_to_year(str(converted_year)) + str_re_form[4:]

        return str_re_form

    @staticmethod
    def _chop_ref(rawstring):
        str_re_value = re.sub('<ref>.+</ref>', '', rawstring)
        str_re_value = re.sub(r'\{\{CRef\|.+\}\}', '', str_re_value)
        return str_re_value

    @staticmethod
    def _append_zeros_to_year(year):
        for i in range((4 - len(year))):
            year = '0' + year
        return year

    @staticmethod
    def _month_to_int(month):
        try:
            month_int = int(month)
            if month_int < 10:
                return '0' + str(month_int)
            else:
                return str(month_int)
        except Exception:
            try:
                return month_mapping[month]
            except:
                raise ValueError(month)

    @staticmethod
    def _day_to_int(day):
        try:
            day_int = int(day)
            if day_int < 10:
                return '0' + str(day_int)
            else:
                return str(day_int)
        except Exception:
            raise ValueError(day)
