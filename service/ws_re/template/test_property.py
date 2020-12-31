# pylint: disable=no-self-use,protected-access
from unittest import TestCase

from testfixtures import compare

from service.ws_re.template.property import Property


class TestReProperty(TestCase):
    def test_init(self):
        re_property = Property(name="Test", default=False)
        self.assertFalse(re_property.value)
        re_property.value = True
        self.assertTrue(re_property.value)
        with self.assertRaises(TypeError):
            re_property.value = "other"

    def test_format_bool(self):
        re_property = Property(name="Test", default=False)
        self.assertEqual(re_property.value_to_string(), "OFF")
        re_property.value = True
        self.assertEqual(re_property.value_to_string(), "ON")

    def test_wrong_default(self):
        with self.assertRaises(TypeError):
            re_property = Property(name="Test", default=1)
            re_property.value_to_string()

    def test_set_bool_with_ON_and_OFF(self):
        re_property = Property(name="Test", default=False)
        re_property.value = "ON"
        self.assertTrue(re_property.value)
        re_property.value = "OFF"
        self.assertFalse(re_property.value)
        re_property.value = ""
        self.assertFalse(re_property.value)

    def test_set_bool_bug_non_capitalized(self):
        re_property = Property(name="Test", default=False)
        re_property.value = "on"
        self.assertTrue(re_property)

    def test_set_value_not_stripped(self):
        re_property = Property(name="Test", default=False)
        re_property.value = "ON         "
        self.assertTrue(re_property)
        re_property_text = Property(name="Text", default="")
        re_property_text.value = "foo              "
        compare("foo", re_property_text.value)

    def test_hash(self):
        re_property = Property(name="Test", default=False)
        pre_hash = hash(re_property)
        re_property.value = True
        self.assertNotEqual(pre_hash, hash(re_property))

        re_property = Property(name="Test", default="")
        pre_hash = hash(re_property)
        re_property.value = "value"
        self.assertNotEqual(pre_hash, hash(re_property))

    def test_repr(self):
        re_property = Property(name="Test", default=False)
        compare("<Property (name: Test, value: False, type: bool)>", repr(re_property))
