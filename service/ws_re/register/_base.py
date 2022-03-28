from pathlib import Path

_REGISTER_PATH: Path = Path(__file__).parent.joinpath("data")


class RegisterException(Exception):
    pass
