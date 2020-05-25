import os
from unittest import skipUnless

from timeout_decorator import timeout


def wikidata_test(func):
    # pylint: disable=no-value-for-parameter
    # todo: improve this https://stackoverflow.com/questions/11349183/how-to-wrap-every-method-of-a-class
    wrapper = timeout(5,
                      timeout_exception=AssertionError,
                      exception_message="Test took to long. Wikidatas Maxlag is too high.",
                      use_signals=False)(func)
    return wrapper


REAL_DATA_TEST = "WS_REAL_DATA" in os.environ
REAL_WIKI_TEST = "WS_REAL_WIKI" in os.environ


def real_wiki_test(func):
    wrapper = skipUnless(REAL_WIKI_TEST, "only execute in test against real wiki")(func)
    return wrapper
