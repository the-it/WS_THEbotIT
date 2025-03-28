import re

MONTH_MAPPING = {"Januar": "01",
                 "Jänner": "01",
                 "Februar": "02",
                 "März": "03",
                 "April": "04",
                 "Mai": "05",
                 "Juni": "06",
                 "Juli": "07",
                 "August": "08",
                 "September": "09",
                 "Oktober": "10",
                 "November": "11",
                 "Dezember": "12",
                 "Jan": "01",
                 "Feb": "02",
                 "Mär": "03",
                 "Apr": "04",
                 "Jun": "06",
                 "Jul": "07",
                 "Aug": "08",
                 "Sept": "09",
                 "Okt": "10",
                 "Nov": "11",
                 "Dez": "12",
                 "1.": "01",
                 "2.": "02",
                 "3.": "03",
                 "4.": "04",
                 "5.": "05",
                 "6.": "06",
                 "7.": "07",
                 "8.": "08",
                 "9.": "09",
                 "10.": "10",
                 "11.": "11",
                 "12.": "12"}


class DateConversion:
    def __init__(self, rawstring):
        self.rawstring = rawstring

    _months = "Jan|Jän|Feb|Mär|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Nov|Dez"
    regex_dont_know = re.compile(r"(unbekannt|Unbekannt|\?)")
    regex_preset = re.compile(r"<!--(\d{4}-\d{2}-\d{2})-->")
    regex_before_domino = re.compile(r"v. Chr")
    regex_only_century = re.compile(r"(\d{1,2})\. (Jahrhundert|Jh.)")
    regex_complete_date = \
        re.compile(r"\d{1,2}(\.|\. | )(\d\d?|" + _months + r")\w*(\.|\. | )(\d{1,4})")
    regex_no_day = re.compile(r"(\d{1,2}\.|" + _months + r")\w*(\.|\. | )(\d{1,4})")
    regex_only_year = re.compile(r"\d{1,4}")

    def __str__(self):
        # chop the unused parts of the string
        str_re_form = self._chop_ref(self.rawstring)
        str_re_form = self._chop_jul(str_re_form)
        str_re_form = self._chop_unsure(str_re_form)
        # sort for structure of the information and interpred it
        if match := self.regex_preset.search(str_re_form):
            return_str = match.group(1)
        elif match := self.regex_only_century.search(str_re_form):
            # Case: only a century given
            if self.regex_before_domino.search(str_re_form):
                century_int = int(match.group(1))
            else:
                century_int = int(match.group(1)) - 1
            year = (str(century_int) + "00").zfill(4)
            return_str = "".join([year, "-", "00", "-", "00"])
            del year
        elif match := self.regex_complete_date.search(str_re_form):
            # Case: complete date
            li_str = re.split("[. ]{1,2}", match.group())
            li_str[0] = self._day_to_int(re.sub(r"\.", "", li_str[0]))  # remove dot from day
            li_str[1] = self._month_to_int(li_str[1])  # Monat in Zahl verwandeln
            li_str[2] = li_str[2].zfill(4)  # append zeros to the year
            return_str = "".join([li_str[2], "-", li_str[1], "-", li_str[0]])
        elif match := self.regex_no_day.search(str_re_form):
            # Case: only month and year
            li_str = re.split(" ", match.group())
            li_str[0] = self._month_to_int(li_str[0])  # Monat in Zahl verwandeln
            li_str[1] = li_str[1].zfill(4)  # append zeros to the year
            return_str = "".join([li_str[1], "-", li_str[0], "-", "00"])
        elif match := self.regex_only_year.search(str_re_form):
            # Case: only year
            li_str = re.split(" ", match.group())
            li_str[0] = li_str[0].zfill(4)  # append zeros to the year
            return_str = "".join([li_str[0], "-", "00", "-", "00"])
        elif str_re_form == "" or self.regex_dont_know.search(str_re_form):
            # Case: empty rawstring
            return_str = "Z-00-00"
        else:
            raise ValueError(str_re_form)

        # interpret the information of v. Chr.
        if self.regex_before_domino.search(str_re_form):
            year_int = int(return_str[0:4])
            converted_year = 9999 - year_int
            return_str = "-" + str(converted_year).zfill(4) + return_str[4:]

        return return_str

    @staticmethod
    def _chop_ref(rawstring):
        str_re_value = re.sub("<ref>.+</ref>", "", rawstring)
        str_re_value = re.sub(r"{{CRef\|.+}}", "", str_re_value)
        return str_re_value

    @staticmethod
    def _chop_jul(rawstring):
        str_re_value = re.sub(r"(?:\(jul.\)|\(greg.\)) ?", "", rawstring)
        return str_re_value

    @staticmethod
    def _chop_unsure(rawstring):
        str_re_value = re.sub(r"\(\?\) ?", "", rawstring)
        return str_re_value

    @staticmethod
    def _month_to_int(month):
        try:
            month_int = int(month)
            return str(month_int).zfill(2)
        except ValueError:
            try:
                return MONTH_MAPPING[month]
            except IndexError as error:
                raise ValueError(month) from error

    @staticmethod
    def _day_to_int(day):
        day_int = int(day)
        return str(day_int).zfill(2)
