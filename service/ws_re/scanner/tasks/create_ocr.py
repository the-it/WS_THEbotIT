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

    def task(self):
        return True

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



