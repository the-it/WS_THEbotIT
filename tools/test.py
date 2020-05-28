import os
from unittest import skipUnless

REAL_DATA_TEST = "WS_REAL_DATA" in os.environ
REAL_WIKI_TEST = "WS_REAL_WIKI" in os.environ


def real_wiki_test(func):
    wrapper = skipUnless(REAL_WIKI_TEST, "only execute in test against real wiki")(func)
    return wrapper
