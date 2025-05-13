import re
from typing import Union

from service.ws_re.template.article import Article

_REGEX_REDIRECT_RAW = r"(?:\[\[RE:|\{\{RE siehe\|)([^\|\}]+)"
_REGEX_REDIRECT = re.compile(_REGEX_REDIRECT_RAW)
_REGEX_REDIRECT_PICKY = re.compile(r"s\..*?" + _REGEX_REDIRECT_RAW)


def get_redirect(article: Article) -> Union[bool, str]:
    redirect = article["VERWEIS"].value
    if redirect:
        match = _REGEX_REDIRECT.findall(article.text)
        if match:
            # if there are more then one result get more picky
            if len(match) == 1:
                redirect = match[0]
            # be more picky and look for a s. ...
            else:
                match = _REGEX_REDIRECT_PICKY.findall(article.text)
                # if there are still too much results, we return just the truth value
                if len(match) == 1:
                    redirect = match[0]
    return redirect
