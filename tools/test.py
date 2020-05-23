import os
from unittest import skipUnless

from timeout_decorator import timeout_decorator


def wikidata_test(func):
    wrapper = timeout_decorator.timeout(2,
                                        timeout_exception=AssertionError,
                                        exception_message="Test took to long. Wikidata seems to be down")(func)
    return wrapper

REAL_DATA_TEST = "WS_REAL_DATA" in os.environ
REAL_WIKI_TEST = "WS_REAL_WIKI" in os.environ

@skipUnless(REAL_WIKI_TEST, "only execute in integration test")

def real_wiki_test(func):
    wrapper = skipUnless(REAL_WIKI_TEST, "only execute in test against real wiki")(func)
    return wrapper

