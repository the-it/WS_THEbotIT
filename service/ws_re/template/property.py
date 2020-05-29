from typing import Optional

from service.ws_re.template._typing import PropertyValueType


class Property:
    def __init__(self, name: str, default: PropertyValueType):
        self._name = name
        self._default: PropertyValueType = default
        self._value: Optional[PropertyValueType] = None

    def _return_by_type(self, value: PropertyValueType) -> PropertyValueType:
        ret = value
        if not isinstance(self._default, (bool, str)):
            raise TypeError(f"Default value ({self._default}) is invalid")
        if isinstance(self._default, bool):
            if value:
                ret = "ON"
            else:
                ret = "OFF"
        return ret

    @staticmethod
    def _set_bool_by_str(on_off: str) -> bool:
        ret = False
        if on_off in ("ON", "on"):
            return True
        return ret

    @property
    def value(self) -> PropertyValueType:
        if self._value:
            ret = self._value
        else:
            ret = self._default
        return ret

    @value.setter
    def value(self, new_value: PropertyValueType):
        if isinstance(new_value, str):
            new_value = new_value.strip()
        if isinstance(new_value, type(self._default)):
            self._value = new_value
        elif new_value in ("ON", "OFF", "", "on", "off") \
                and isinstance(new_value, str) \
                and isinstance(self._default, bool):
            if new_value == "":
                self._value = self._default
            self._value = self._set_bool_by_str(new_value)
        else:
            raise TypeError(f"Value ({new_value}) is not the type "
                            f"of default value ({self._default})")

    @property
    def name(self) -> str:
        return self._name

    def value_to_string(self):
        return self._return_by_type(self.value)

    def __hash__(self):
        return hash(self.name) + hash(self.value)

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} (name: {self.name}, value: {self.value}, " \
            f"type: {type(self._default).__name__})>"
