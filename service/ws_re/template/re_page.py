import re
from typing import Optional

import pywikibot

from service.ws_re.template import ReDatenException
from service.ws_re.template.article import Article
from service.ws_re.template.re_page_abstract import RePageAbstract


class RePage(RePageAbstract):
    def __init__(self, wiki_page: pywikibot.Page):
        super().__init__(wiki_page)

    def clean_articles(self):
        """
        removes all articles that are essentially empty strings
        """
        new_list = []
        for article in self._article_list:
            if article:
                new_list.append(article)
        self._article_list = new_list

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
                    self.page.save(summary=reason, botflag=True)
                except pywikibot.exceptions.LockedPage as error:
                    raise ReDatenException(f"Page {self.page.title} is locked, it can't be saved.") from error
            else:
                raise ReDatenException(f"Page {self.page.title} is protected for normal users, "
                                       f"it can't be saved.")

    def append(self, new_article: Article):
        if isinstance(new_article, Article):
            self._article_list.append(new_article)
        else:
            raise TypeError("You can only append Elements of the type ReArticle")

    @property
    def complex_construction(self) -> bool:
        """
        todo: make this obsolete by construction the page as rendered in wiki
        raise a flag is the page has a complex construction, marked by sub lemmas inserted via ... {{#lst: ...
        """
        return bool(re.search(r"\{\{#lst:", self.page.text))

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
