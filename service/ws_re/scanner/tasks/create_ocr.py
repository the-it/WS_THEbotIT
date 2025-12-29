import re
from functools import lru_cache
from typing import cast, Optional

import boto3
import pywikibot
from botocore.exceptions import ClientError

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.base import get_aws_credentials, is_aws_test_env
from tools.bots.logger import WikiLogger


class NoRawOCRFound(Exception):
    pass


class COCRTask(ReScannerTask):
    counter = 0
    bucket_name = "wiki-bots-re-ocr-tst" if is_aws_test_env() else "wiki-bots-re-ocr-prd"
    _ocr_category = "RE:OCR_erstellt"
    _error_category = "RE:OCR_Seite_nicht_gefunden"
    _cut_category = "RE:OCR_nicht_zugeschnitten"
    # Precompile regex patterns used by _detect_empty_content to avoid recompilation on each call
    _re_bold_headers = re.compile(r"'''.*?'''", re.DOTALL)
    _re_seite_template = re.compile(r"\{\{Seite\|[^}]*\}\}")
    _re_ellipsis_placeholders = re.compile(r"(?:\[\s*(?:\.{3}|…)\s*\]|…+|\.{3,})")
    _re_square_brackets = re.compile(r"[\[\]]")
    _re_punct_only_line = re.compile(r"^[\W_]+$")

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        key, secret = get_aws_credentials()
        self.s3_client = boto3.client("s3", aws_access_key_id=key, aws_secret_access_key=secret)

    def task(self):
        if "RE:Stammdaten überprüfen" in self.re_page.page.text:
            return True
        for article_list in self.re_page.splitted_article_list:
            article = cast(Article, article_list[0])
            # don't create if there is already a created
            if self.counter > 8 or self._ocr_category in article.text:
                return True
            if article["KORREKTURSTAND"].value == "Platzhalter" and article.common_free:
                if self._detect_empty_content(article.text):
                    if ocr := self._get_text_for_article(article):
                        article.text = article.text + f"\n{ocr}"
                        self.counter += 1
        return True

    def _get_text_for_section(self, issue: str, page: int, start: bool = False, end: bool = False) -> Optional[str]:
        try:
            raw_text = self.get_raw_page(f"{issue}_{str(page).zfill(4)}").replace("\ufeff", "")
        except NoRawOCRFound:
            return None
        if start:
            match = re.findall(rf"== {self.re_page.lemma} ==(.*?)(?:\n==|$)", raw_text, re.DOTALL)
            if match:
                return str(match[0]).strip()
        if end:
            match = re.findall(r"^(.*?)(?:\n==|$)", raw_text, re.DOTALL)
            if match:
                return str(match[0]).strip()
        return raw_text

    def _get_text_for_article(self, article: Article) -> str:
        """
        Build the article text by stitching OCR sections across the page range.
        - issue is derived from article["BAND"].value
        - pages are from SPALTE_START .. SPALTE_END (inclusive)
        - first page called with start=True, last page with end=True
        """
        # Derive issue identifier
        issue = str(article["BAND"].value)
        # Determine page range
        start_str = str(article["SPALTE_START"].value)
        end_raw = article["SPALTE_END"].value
        end_str = "" if (end_raw is None) or (end_raw == "OFF") else str(end_raw)
        start_page = int(start_str)
        end_page = int(end_str) if end_str else start_page
        parts: list[str] = [f"[[Kategorie:{self._cut_category}]]"]
        for page in range(start_page, end_page + 1):
            txt = self._get_text_for_section(
                issue,
                page,
                start=(page == start_page),
                end=(page == end_page)
            )
            if page != start_page:
                parts.append(f"{{{{Seite|{page}||{{{{REEL|{issue}|{page}}}}}}}}}")
            if txt:
                parts.append(txt.strip())
            else:
                parts.append(f"[[Kategorie:{self._error_category}]]")
        return f"[[Kategorie:{self._ocr_category}]]\n" + "\n".join(parts)

    def _detect_empty_content(self, text: str) -> bool:
        """
        Detect if the first article on the current RePage has no meaningful content.
        Consider as empty when only placeholder markers (e.g., "[...]"), page markers
        like {{Seite|...}}, formatting (e.g., bold title) or a small stub (endding on etc. etc.)
        are present.
        """
        # Remove bold headers entirely
        text = self._re_bold_headers.sub("", text)
        # Remove Seite templates completely
        text = self._re_seite_template.sub("", text)
        # Remove common placeholder ellipses variants (bracketed or standalone) in one pass
        text = self._re_ellipsis_placeholders.sub("", text)
        # Remove any remaining brackets that may linger from placeholders
        text = self._re_square_brackets.sub("", text)
        # Remove empty lines and stray punctuation-only lines
        lines = [self._re_punct_only_line.sub("", ln.strip()) for ln in text.splitlines()]
        text = "\n".join([ln for ln in lines if ln]).strip()

        if text and text[-9:] == "etc. etc." and len(text) < 200:
            return True

        # After cleaning, if nothing meaningful remains, it's empty
        return len(text) == 0

    @lru_cache(maxsize=1000)
    def get_raw_page(self, page_id: str) -> str:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=f"{page_id}.txt")
            return response["Body"].read().decode("utf-8")
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                raise NoRawOCRFound(f'Page_ID {page_id} not found in OCR bucket') from ex
            raise
