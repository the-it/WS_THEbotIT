import re
from datetime import timedelta, datetime

from math import ceil
from pywikibot import ItemPage, Page, Site

from tools.bots import CanonicalBot
from tools.date_conversion import DateConversion
from tools.petscan import PetScan
from tools.template_handler import TemplateHandler


class AuthorList(CanonicalBot):
    # pylint: disable=bare-except,too-many-branches,broad-except
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.searcher = PetScan()
        self.repo = self.wiki.data_repository()  # this is a DataSite object
        self.string_list = []
        self.match_property = re.compile(r"\{\{#property:P(\d{1,4})\}\}")
        self.number_to_month = {1: "Januar",
                                2: "Februar",
                                3: "März",
                                4: "April",
                                5: "Mai",
                                6: "Juni",
                                7: "Juli",
                                8: "August",
                                9: "September",
                                10: "Oktober",
                                11: "November",
                                12: "Dezember"}

    def __enter__(self):
        CanonicalBot.__enter__(self)
        if self.timestamp.start_of_run.day == 1:
            self.data.assign_dict(dict())
            self.logger.warning("The data is thrown away. It is the first of the month")
        return self

    def task(self):
        lemma_list = self._run_searcher()
        self._build_database(lemma_list)
        if self.debug:
            dump = Page(self.wiki, f"Benutzer:THEbotIT/{self.bot_name}")
        else:
            dump = Page(self.wiki, "Liste der Autoren")
        old_text = dump.text
        new_text = self._convert_to_table()
        if new_text[150:] != old_text[150:]:  # compare all but the date
            dump.text = new_text
            dump.save("Die Liste wurde auf den aktuellen Stand gebracht.", botflag=True)
        else:
            self.logger.info("Heute gab es keine Änderungen, "
                             "daher wird die Seite nicht überschrieben.")
        return True

    def _run_searcher(self):
        # was the last run successful
        if self.debug:
            # if False
            yesterday = datetime.now() - timedelta(days=5)
            self.searcher.last_change_after(datetime(year=int(yesterday.strftime("%Y")),
                                                     month=int(yesterday.strftime("%m")),
                                                     day=int(yesterday.strftime("%d"))))
        elif self.last_run_successful and self.data:
            start_of_search = self.create_timestamp_for_search()
            self.searcher.last_change_after(start_of_search)
            self.logger.info(f"The date {start_of_search.strftime('%d.%m.%Y')} "
                             f"is set to the argument \"after\".")
        else:
            self.logger.warning("There was no timestamp found of the last run, "
                                "so the argument \"after\" is not set.")
        self.searcher.add_namespace(0)  # search in main namespace
        self.searcher.add_positive_category("Autoren")
        self.searcher.add_yes_template("Personendaten")
        self.searcher.get_wikidata_items()

        self.logger.debug(self.searcher)

        entries_to_search = self.searcher.run()
        return entries_to_search

    _space_regex = re.compile(r"\s+")

    def _strip_spaces(self, raw_string: str):
        return self._space_regex.subn(raw_string.strip(), " ")[0]

    def _build_database(self, lemma_list):
        # pylint: disable=too-many-statements
        for idx, author in enumerate(lemma_list):
            self.logger.debug(f"{idx + 1}/{len(lemma_list)} {author['title']}")
            # delete preexisting data of this author
            try:
                del self.data[str(author["id"])]
            except KeyError:
                if self.last_run_successful:
                    self.logger.info(f"Can't delete old entry of [[{author['title']}]]")

            dict_author = {"title": author["title"]}
            # extract the Personendaten-block form the wikisource page
            page = Page(self.wiki, author["title"])
            try:
                try:
                    personendaten = re.search(r"\{\{Personendaten(?:.|\n)*?\n\}\}\n",
                                              page.text).group()
                except AttributeError:
                    self.logger.error(f"No valid block \"Personendaten\" was found for "
                                      f"[[{author['title']}]].")
                    personendaten = None
                if personendaten:
                    # personendaten = re.sub('<ref.*?>.*?<\/ref>|<ref.*?\/>', '', personendaten)
                    # personendaten = re.sub('\{\{CRef|.*?(?:\{\{.*?\}\})?}}', '', personendaten)
                    template_extractor = TemplateHandler(personendaten)
                    dict_author.update({"name": self._strip_spaces(
                        template_extractor.get_parameter("NACHNAME")["value"])})
                    dict_author.update({"first_name": self._strip_spaces(
                        template_extractor.get_parameter("VORNAMEN")["value"])})
                    try:
                        dict_author.update({"birth": self._strip_spaces(
                            template_extractor.get_parameter("GEBURTSDATUM")["value"])})
                    except Exception:
                        dict_author.update({"birth": ""})
                        self.logger.warning(f"Templatehandler couldn't find a birthdate for: "
                                            f"[[{author['title']}]]")
                    try:
                        dict_author.update({"death": self._strip_spaces(
                            template_extractor.get_parameter("STERBEDATUM")["value"])})
                    except Exception:
                        dict_author.update({"death": ""})
                        self.logger.warning(f"Templatehandler couldn't find a deathdate for: "
                                            f"[[{author['title']}]]")
                    try:
                        dict_author.update(
                            {"description":
                             template_extractor.get_parameter("KURZBESCHREIBUNG")["value"]})
                    except Exception:
                        dict_author.update({"description": ""})
                        self.logger.warning(
                            f"Templatehandler couldn't find a description for: "
                            f"[[{author['title']}]]")
                    try:
                        dict_author.update(
                            {"synonyms":
                             template_extractor.get_parameter("ALTERNATIVNAMEN")["value"]})
                    except Exception:
                        dict_author.update({"synonyms": ""})
                        self.logger.warning(f"Templatehandler couldn't find synonyms for: "
                                            f"[[{author['title']}]]")
                    try:
                        dict_author.update(
                            {"sortkey": template_extractor.get_parameter("SORTIERUNG")["value"]})
                        if dict_author["sortkey"] == "":
                            raise ValueError
                    except Exception:
                        self.logger.debug("there is no sortkey for [[{}]].".format(author["title"]))
                        # make a dummy key
                        if not dict_author["name"]:
                            dict_author["sortkey"] = dict_author["first_name"]
                            self.logger.warning("Author has no last name.")
                        elif not dict_author["first_name"]:
                            dict_author["sortkey"] = dict_author["name"]
                            self.logger.warning("Author has no last first_name.")
                        else:
                            dict_author["sortkey"] = \
                                dict_author["name"] + ", " + dict_author["first_name"]
                    try:
                        dict_author.update({"wikidata": author["q"]})
                    except KeyError:
                        self.logger.warning(f"The autor [[{author['title']}]] has no wikidata_item")
                    self.data.update({author["id"]: dict_author})
            except Exception as exception:
                self.logger.exception("Exception not catched: ", exc_info=exception)
                self.logger.error(f"author {author['title']} have a problem")

    @staticmethod
    def _sort_author_list(list_authors):
        list_authors.sort(key=lambda x: x[0])
        for i in range(len(list_authors) - 1):
            if list_authors[i][0] == list_authors[i + 1][0]:
                equal_count = 2
                while True:
                    if i + equal_count <= len(list_authors):
                        if list_authors[i][0] != list_authors[i + equal_count][0]:
                            break
                        equal_count += 1
                temp_list = list_authors[i:i + equal_count]
                temp_list.sort(key=lambda x: x[5])  # sort by birth date
                list_authors[i:i + equal_count] = temp_list

    def _convert_to_table(self):
        # pylint: disable=too-many-locals
        # make a list of lists
        self.logger.info("Start compiling.")
        list_authors = []
        for key in self.data:
            author_dict = self.data[key]
            list_author = list()
            list_author.append(author_dict["sortkey"])  # 0
            list_author.append(author_dict["title"].replace("_", " "))  # 1
            list_author.append(author_dict["name"])  # 2
            list_author.append(author_dict["first_name"])  # 3

            for event in ["birth", "death"]:
                list_author.append(self._handle_birth_and_death(event, author_dict))  # 4,6
                try:
                    list_author.append(str(DateConversion(list_author[-1])))  # 5,7
                except ValueError:
                    self.logger.error(f"Can´t compile sort key for {author_dict['title']}: "
                                      f"{event}/{author_dict[event]}")
                    list_author.append("!-00-00")  # 5,7
            list_author.append(author_dict["description"])  # 8
            list_authors.append(list_author)

        # sorting the list
        self.logger.info("Start sorting.")
        self._sort_author_list(list_authors)

        self.logger.info("Start printing.")
        dt = self.timestamp.start_of_run
        self.string_list.append(f"Diese Liste der Autoren enthält alle {len(self.data)}<ref>Stand: "
                                f"{dt.day}.{dt.month}.{dt.year}, "
                                f"{self.timestamp.start_of_run.strftime('%H:%M')} (UTC)</ref> Autoren, "
                                f"zu denen in Wikisource eine Autorenseite existiert.")
        self.string_list.append("Die Liste kann mit den Buttons neben den Spaltenüberschriften"
                                " nach der jeweiligen Spalte sortiert werden.")
        self.string_list.append("<!--")
        self.string_list.append("Diese Liste wurde durch ein Computerprogramm erstellt, "
                                "das die Daten verwendet, "
                                "die aus den Infoboxen auf den Autorenseiten stammen.")
        self.string_list.append("Sollten daher Fehler vorhanden sein, "
                                "sollten diese jeweils dort korrigiert werden.")
        self.string_list.append("-->")
        self.string_list.append("{|class=\"wikitable sortable\"")
        self.string_list.append("!style=\"width:20%\"| Name")
        self.string_list.append("!data-sort-type=\"text\" style=\"width:15%\"| Geb.-datum")
        self.string_list.append("!data-sort-type=\"text\" style=\"width:15%\"| Tod.-datum")
        self.string_list.append("!class=\"unsortable\" style=\"width:50%\"| Beschreibung")
        for list_author in list_authors:
            aut_sort, aut_page, aut_sur, aut_pre, birth_str, \
                birth_sort, death_str, death_sort, description = \
                list_author
            self.string_list.append("|-")
            if aut_sur and aut_pre:
                self.string_list.append(f"|data-sort-value=\"{aut_sort}\"|"
                                        f"[[{aut_page}|{aut_sur}, {aut_pre}]]")
            elif aut_pre:
                self.string_list.append(f"|data-sort-value=\"{aut_sort}\"|[[{aut_page}|{aut_pre}]]")
            else:
                self.string_list.append(f"|data-sort-value=\"{aut_sort}\"|[[{aut_page}|{aut_sur}]]")
            self.string_list.append(f"|data-sort-value=\"{birth_sort}\"|{birth_str}")
            self.string_list.append(f"|data-sort-value=\"{death_sort}\"|{death_str}")
            self.string_list.append(f"|{description}")
        self.string_list.append("|}")
        self.string_list.append('')
        self.string_list.append("== Anmerkungen ==")
        self.string_list.append("<references/>")
        self.string_list.append('')
        self.string_list.append("{{SORTIERUNG:Autoren #Liste der}}")
        self.string_list.append("[[Kategorie:Listen]]")
        self.string_list.append("[[Kategorie:Autoren|!]]")

        return "\n".join(self.string_list)

    def _handle_birth_and_death(self, event, author_dict):
        if author_dict[event] == '' or self.match_property.search(author_dict[event]):
            self.logger.debug(f"No valid entry in {event} for "
                              f"[[{author_dict['title']}]] ... Fallback to wikidata")
            try:
                item = ItemPage(self.repo, author_dict["wikidata"])
                if event == "birth":
                    property_label = "P569"
                else:
                    property_label = "P570"
                claim = item.text["claims"][property_label][0]
                date_from_data = claim.getTarget()
                if date_from_data.precision < 7:
                    self.logger.error("Precison is to low for [[{}]]".format(author_dict['title']))
                elif date_from_data.precision < 8:
                    date_from_data = int(ceil(float(date_from_data.year) / 100.0) * 100)
                    if date_from_data < 1000:
                        date_from_data = str(date_from_data)[0:1] + ". Jh."
                    else:
                        date_from_data = str(date_from_data)[0:2] + ". Jh."
                elif date_from_data.precision < 10:
                    date_from_data = str(date_from_data.year)
                elif date_from_data.precision < 11:
                    date_from_data = self.number_to_month[date_from_data.month] + " " + \
                        str(date_from_data.year)
                else:
                    date_from_data = f"{date_from_data.day}. " \
                        f"{self.number_to_month[date_from_data.month]} " \
                        f"{date_from_data.year}"
                if re.search("-", date_from_data):
                    date_from_data = date_from_data.replace("-", "") + " v. Chr."
                self.logger.debug(f"Found {date_from_data} @ wikidata for {event}")
                return date_from_data  # 4,6
            except Exception:
                self.logger.debug("Wasn't able to ge any data from wikidata")
                return ''  # 4,6
        else:
            return author_dict[event]  # 4,6


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with AuthorList(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
