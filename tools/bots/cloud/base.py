import os
from typing import Tuple


def is_aws_test_env() -> bool:
    return "WS_AWS_TST_ENV" in os.environ


def get_aws_credentials() -> Tuple[str, str]:
    if "WS_AWS_TST_ENV" in os.environ:
        return os.environ["WS_AWS_TST_KEY"], os.environ["WS_AWS_TST_SECRET"]
    if "WS_AWS_PRD_ENV" in os.environ:
        return os.environ["WS_AWS_PRD_KEY"], os.environ["WS_AWS_PRD_SECRET"]
    # if no valid env is present, just go with bogo keys
    return "", ""
