import re
from datetime import datetime
from functools import lru_cache
from typing import cast, Optional

import boto3
import pywikibot
from botocore.exceptions import ClientError

from service.ws_re.register.lemma import Lemma
from service.ws_re.scanner.tasks.base_task import ReScannerTask, ReporterMixin
from service.ws_re.template.article import Article
from tools.bots.base import get_aws_credentials
from tools.bots.logger import WikiLogger


class NoRawOCRFound(Exception):
    pass


class COCRTask(ReScannerTask):
    _bucket_name = "wiki-bots-re-ocr-prd"
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        key, secret = get_aws_credentials()
        self.s3_client = boto3.client("s3", aws_access_key_id=key, aws_secret_access_key=secret)
        # Precompile regex patterns used by _detect_empty_content to avoid recompilation on each call
        self._re_bold_headers = re.compile(r"'''.*?'''", re.DOTALL)
        self._re_seite_template = re.compile(r"\{\{Seite\|[^}]*\}\}")
        self._re_ellipsis_placeholders = re.compile(r"(?:\[\s*(?:\.{3}|…)\s*\]|…+|\.{3,})")
        self._re_square_brackets = re.compile(r"[\[\]]")
        self._re_punct_only_line = re.compile(r"^[\W_]+$")

    def task(self):


    def _get_text_for_section(self, issue: str, page: int, start: bool=False, end: bool=False) -> Optional[str]:
        try:
            raw_text = self.get_raw_page(f"{issue}_{str(page).zfill(4)}")
        except NoRawOCRFound:
            return None
        if start:
            match = re.findall(rf"== {self.re_page.lemma} ==(.*?)(?:\n==|$)", raw_text, re.DOTALL)
            if match:
                return match[0].strip()
        if end:
            match = re.findall(rf"^(.*?)(?:\n==|$)", raw_text, re.DOTALL)
            if match:
                return match[0].strip()
        return raw_text

    def _detect_empty_content(self) -> bool:
        """
        Detect if the first article on the current RePage has no meaningful content.
        Consider as empty when only placeholder markers (e.g., "[...]"), page markers
        like {{Seite|...}}, formatting (e.g., bold title) or a small stub (endding on etc. etc.)
        are present.
        """
        # Prefer structured access to the first article's text
        content = self.re_page.first_article.text
        if not content:
            return True

        cleaned = content
        # Remove bold headers entirely
        cleaned = self._re_bold_headers.sub("", cleaned)
        # Remove Seite templates completely
        cleaned = self._re_seite_template.sub("", cleaned)
        # Remove common placeholder ellipses variants (bracketed or standalone) in one pass
        cleaned = self._re_ellipsis_placeholders.sub("", cleaned)
        # Remove any remaining brackets that may linger from placeholders
        cleaned = self._re_square_brackets.sub("", cleaned)
        # Remove empty lines and stray punctuation-only lines
        lines = [self._re_punct_only_line.sub("", ln.strip()) for ln in cleaned.splitlines()]
        cleaned = "\n".join([ln for ln in lines if ln]).strip()

        if cleaned and cleaned[-9:] == "etc. etc." and len(cleaned) < 200:
            return True

        # After cleaning, if nothing meaningful remains, it's empty
        return len(cleaned) == 0

    @lru_cache(maxsize=1000)
    def get_raw_page(self, page_id: str) -> str:
        try:
            response = self.s3_client.get_object(Bucket=self._bucket_name, Key=f"{page_id}.txt")
            return response["Body"].read().decode("utf-8")
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                raise NoRawOCRFound(f"Page_ID {page_id} not found in OCR bucket")
            else:
                raise



