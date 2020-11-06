from abc import ABC, abstractmethod
from typing import List, Union

import pywikibot

from service.ws_re.template import RE_DATEN, RE_ABSCHNITT, RE_AUTHOR, ReDatenException
from service.ws_re.template.article import Article
from tools.template_finder import TemplateFinder, TemplateFinderException


class RePageAbstract(ABC):
    def __init__(self, wiki_page: pywikibot.Page):
        self.page: pywikibot.Page = wiki_page
        self._pre_text: str = self.page.text
        self._article_list: List[Union[Article, str]] = list()
        self._init_page_dict()

    def _init_page_dict(self):
        # find the positions of all key templates
        template_finder = TemplateFinder(self._pre_text)
        try:
            re_daten_pos = template_finder.get_positions(RE_DATEN)
            re_abschnitt_pos = template_finder.get_positions(RE_ABSCHNITT)
            re_author_pos = template_finder.get_positions(RE_AUTHOR)
        except TemplateFinderException as error:
            raise ReDatenException("There are corrupt templates.") from error
        re_starts = re_daten_pos + re_abschnitt_pos
        re_starts.sort(key=lambda x: x["pos"][0])
        if not re_starts:
            raise ReDatenException("No single start template found.")
        if len(re_starts) != len(re_author_pos):
            raise ReDatenException(
                "The count of start templates doesn't match the count of end templates.")
        # iterate over start and end templates of the articles and create ReArticles of them
        last_handled_char = 0
        for pos_daten, pos_author in zip(re_starts, re_author_pos):
            if last_handled_char < pos_daten["pos"][0]:
                # there is plain text in front of the article
                text_to_handle = self._pre_text[last_handled_char:pos_daten["pos"][0]].strip()
                if text_to_handle:
                    # not just whitespaces
                    self._article_list.append(text_to_handle)
            self._article_list.append(
                Article.from_text(self._pre_text[pos_daten["pos"][0]:pos_author["pos"][1]]))
            last_handled_char = pos_author["pos"][1]
        # handle text after the last complete article
        if last_handled_char < len(self._pre_text):
            self._article_list.append(self._pre_text[last_handled_char:len(self._pre_text)].strip())

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} (articles: {len(self), len(self.splitted_article_list)}, " \
            f"lemma: {self.lemma_without_prefix})>"

    def __getitem__(self, idx: int) -> Union[Article, str]:
        return self._article_list[idx]

    def __len__(self) -> int:
        return len(self._article_list)

    def __delitem__(self, idx: int):
        del self._article_list[idx]

    def __setitem__(self, idx: int, item: Union[Article, str]):
        self._article_list[idx] = item

    def __hash__(self):
        hash_value = 0
        for counter, article in enumerate(self._article_list):
            hash_value += hash(article) << counter
        return hash_value

    def __str__(self) -> str:
        articles = []
        for article in self._article_list:
            if isinstance(article, Article):
                articles.append(article.to_text())
            else:  # it is only a string
                articles.append(article)
        return "\n".join(articles)

    @property
    def lemma(self):
        return self.page.title()

    @property
    def lemma_without_prefix(self):
        return self.lemma[3:]

    @property
    def lemma_as_link(self):
        return f"[[{self.lemma}|{self.lemma_without_prefix}]]"

    @property
    def only_articles(self) -> List[Article]:
        return [article for article in self._article_list if isinstance(article, Article)]

    @property
    def first_article(self) -> Article:
        return self.only_articles[0]

    @property
    def splitted_article_list(self) -> List[List[Union[Article, str]]]:
        """
        For some tasks it is helpful to group the list of articles to groups of articles splitted at header articles.

        Example: [RE_Daten, RE_Abschnitt, str, RE_Daten, RE_Daten, str, RE_Abschnitt] ->
                 [[RE_Daten, RE_Abschnitt, str], [RE_Daten], [RE_Daten, str, RE_Abschnitt]]

        :return: a list with lists of articles/strings.
        """
        splitted_list: List[List[Union[Article, str]]] = []
        for article in self._article_list:
            if isinstance(article, Article) and article.article_type == RE_DATEN:
                splitted_list.append([article])
            else:
                try:
                    splitted_list[-1].append(article)
                except IndexError:
                    splitted_list.append([article])
        return splitted_list

    def has_changed(self) -> bool:
        return self._pre_text != str(self)

    @property
    @abstractmethod
    def is_writable(self) -> bool:
        pass
