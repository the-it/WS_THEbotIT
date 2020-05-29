from dataclasses import dataclass


@dataclass
class SnakParameter:
    """
    Class for keeping track of Snak parameters

    :param property_str: Number of the Property, example "P1234"
    :param target_type: Value of the target. Possible values: "wikibase-item", "string", "commonsMedia",
                        "globe-coordinate", "url", "time", "quantity", "monolingualtext", "math", "external-id",
                        "geo-shape", "tabular-data"
    :param target: actual value of the target
    """
    property_str: str
    target_type: str
    target: str
