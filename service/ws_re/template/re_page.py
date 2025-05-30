import re
from typing import Union, Optional, Iterator

import pywikibot

from service.ws_re.template import RE_DATEN, RE_ABSCHNITT, RE_AUTHOR, ReDatenException
from service.ws_re.template.article import Article
from tools.template_finder import TemplateFinderException, TemplateFinder, TemplatePosition


class ArticleList:
    def __init__(self, article_list: list[Article]):
        self.article_list = article_list

    def __getitem__(self, index: int) -> Article:
        return self.article_list[index]

    def __len__(self) -> int:
        return len(self.article_list)

    def __iter__(self) -> Iterator[Article]:
        yield from self.article_list

    def append(self, article: Article):
        self.article_list.append(article)

    @property
    def daten(self) -> Article:
        return self.article_list[0]


class SplittedArticleList:
    def __init__(self, article_list: list[Union[Article, str]]):
        self._article_list = article_list
        self._splitted_list = self._create_splitted_article_list()

    def _create_splitted_article_list(self) -> list[ArticleList]:
        """
        For some tasks it is helpful to group the list of articles to groups of articles splitted at header articles.
        Example: [RE_Daten, RE_Abschnitt, str, RE_Daten, RE_Daten, str, RE_Abschnitt] ->
                 [[RE_Daten, RE_Abschnitt, str], [RE_Daten], [RE_Daten, str, RE_Abschnitt]]
        :return: a list with lists of articles/strings.
        """
        splitted_list: list[ArticleList] = []
        for article in self._article_list:
            if isinstance(article, str):
                continue
            if article.article_type == RE_DATEN:
                splitted_list.append(ArticleList([article]))
            else:
                splitted_list[-1].append(article)
        return splitted_list

    def __len__(self) -> int:
        return len(self._splitted_list)

    def __getitem__(self, index: int) -> ArticleList:
        return self._splitted_list[index]

    def __iter__(self) -> Iterator[ArticleList]:
        yield from self._splitted_list

    @property
    def first_article(self) -> Article:
        return self._splitted_list[0].daten

    @property
    def list(self) -> list[ArticleList]:
        return self._splitted_list


class RePage:
    def __init__(self, wiki_page: pywikibot.Page):
        self.page: pywikibot.Page = wiki_page
        self.pre_text: str = self.page.text
        self._article_list: list[Union[Article, str]] = []
        self._init_page_dict()
        self.splitted_article_list = SplittedArticleList(self._article_list)

    def _init_page_dict(self):
        # find the positions of all key templates
        template_finder = TemplateFinder(self.pre_text)
        try:
            re_daten_pos = template_finder.get_positions(RE_DATEN)
            re_abschnitt_pos = template_finder.get_positions(RE_ABSCHNITT)
            re_author_pos = template_finder.get_positions(RE_AUTHOR)
        except TemplateFinderException as error:
            raise ReDatenException("There are corrupt templates.") from error
        re_starts: list[TemplatePosition] = re_daten_pos + re_abschnitt_pos
        re_starts.sort(key=lambda x: x.start)
        if not re_starts:
            raise ReDatenException("No single start template found.")
        if RE_DATEN not in re_starts[0].text:
            raise ReDatenException("First template isn't of type REDaten. Corrupt structure.")
        if len(re_starts) != len(re_author_pos):
            raise ReDatenException(
                "The count of start templates doesn't match the count of end templates.")
        # iterate over start and end templates of the articles and create ReArticles of them
        last_handled_char = 0
        for pos_daten, pos_author in zip(re_starts, re_author_pos):
            if last_handled_char < pos_daten.start:
                # there is plain text in front of the article
                text_to_handle = self.pre_text[last_handled_char:pos_daten.start].strip()
                if text_to_handle:
                    # not just whitespaces
                    self._article_list.append(text_to_handle)
            self._article_list.append(
                Article.from_text(self.pre_text[pos_daten.start:pos_author.end]))
            last_handled_char = pos_author.end
        # handle text after the last complete article
        if last_handled_char < len(self.pre_text):
            self._article_list.append(self.pre_text[last_handled_char:len(self.pre_text)].strip())

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} (articles: {len(self), len(self.splitted_article_list)}, " \
            f"lemma: {self.lemma_without_prefix})>"

    def __getitem__(self, idx: int) -> Union[Article, str]:
        return self._article_list[idx]

    def __len__(self) -> int:
        return len(self._article_list)

    def __iter__(self) -> Iterator[Union[Article, str]]:
        yield from self._article_list

    def __delitem__(self, idx: int):
        del self._article_list[idx]

    def __setitem__(self, idx: int, item: Union[Article, str]):
        self._article_list[idx] = item

    def __str__(self) -> str:
        articles = []
        for article in self._article_list:
            if isinstance(article, Article):
                articles.append(article.to_text())
            else:  # it is only a string
                articles.append(article)
        return "\n".join(articles)

    def clean_articles(self):
        """
        removes all articles that are essentially empty strings
        """
        new_list = []
        for article in self._article_list:
            if article:
                new_list.append(article)
        self._article_list = new_list

    def has_changed(self) -> bool:
        return self.pre_text != str(self)

    @property
    def is_writable(self) -> bool:
        """
        checks if there is a writing protection on that wiki page, aka only admins are able to edit this page
        """
        protection_dict = self.page.protection()
        if "edit" in protection_dict.keys():
            if protection_dict["edit"][0] == "sysop":
                return False
        return True

    def save(self, reason: str):
        if self.has_changed():
            self.page.text = str(self)
            if self.is_writable:
                try:
                    self.page.save(summary=reason, bot=True)
                except pywikibot.exceptions.LockedPageError as error:
                    raise ReDatenException(f"Page {self.page.title} is locked, it can't be saved.") from error
            else:
                raise ReDatenException(f"Page {self.page.title} is protected for normal users, "
                                       f"it can't be saved.")

    def append(self, new_article: Article):
        if isinstance(new_article, Article):
            self._article_list.append(new_article)
        else:
            raise TypeError("You can only append Elements of the type ReArticle")

    def __hash__(self):
        hash_value = 0
        for counter, article in enumerate(self._article_list):
            hash_value += hash(article) << counter
        return hash_value

    @property
    def lemma(self) -> str:
        return str(self.page.title())

    @property
    def lemma_without_prefix(self) -> str:
        return self.lemma[3:]

    @property
    def lemma_as_link(self) -> str:
        return f"[[{self.lemma}|{self.lemma_without_prefix}]]"

    @property
    def only_articles(self) -> list[Article]:
        return [article for article in self._article_list if isinstance(article, Article)]

    @property
    def first_article(self) -> Article:
        return self.only_articles[0]

    @property
    def complex_construction(self) -> bool:
        """
        todo: make this obsolete by construction the page as rendered in wiki
        raise a flag is the page has a complex construction, marked by sub lemmas inserted via ... {{#lst: ...
        """
        if re.search(r"\{\{#lst:", self.page.text):
            return True
        return False

    def add_error_category(self, category: str, note: Optional[str] = None):
        """
        Adds an error category at the end of the RE lemma

        :param category: the name of the category
        :param note: additional notice, e.g. what error exists
        """
        error = f"[[Kategorie:{category}]]"
        if note:
            error = f"{error}<!--{note}-->"
        if error not in self._article_list[-1]:
            self._article_list.append(error)

    def remove_error_category(self, category: str):
        """
        Remove an existing error category. If no category is set, nothing happens.

        :param category: Category that should be removed
        """
        if isinstance(self._article_list[-1], str):
            self._article_list[-1] = re.sub(rf"\n?\[\[Kategorie:{category}\]\][^\n]*",
                                            "",
                                            self._article_list[-1]).strip()
            if not self._article_list[-1]:
                del self._article_list[-1]

    def get_redirects(self) -> list[pywikibot.Page]:
        return list(self.page.redirects())
