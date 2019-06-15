from unittest import TestCase

from testfixtures import compare

from scripts.service.ws_re.template import ReDatenException
from scripts.service.ws_re.volumes import Volume, Volumes, VolumeType


class TestVolume(TestCase):
    def test_init(self):
        volume = Volume("I,1", "1900", "Aal", "Bethel")
        compare("I,1", volume.name)
        compare("I_1", volume.file_name)
        compare("1900", volume.year)
        compare("Aal", volume.start)
        compare("Bethel", volume.end)

    def test_init_by_name(self):
        volume = Volume(name="I,1", year="1900", start="Aal", end="Bethel")
        compare("I,1", volume.name)
        compare("I_1", volume.file_name)
        compare("1900", volume.year)
        compare("Aal", volume.start)
        compare("Bethel", volume.end)

    def test_init_supp_or_register(self):
        volume = Volume(name="S I", year="1900")
        compare("S I", volume.name)
        compare("1900", volume.year)
        self.assertIsNone(volume.start)
        self.assertIsNone(volume.end)

    def test_init_year_as_int(self):
        volume = Volume(name="S I", year=1900)
        compare("S I", volume.name)
        compare("1900", volume.year)

    def test_volume_type(self):
        volume = Volume("I,1", "1900", "Aal", "Bethel")
        compare(VolumeType.FIRST_SERIES, volume.type)
        volume = Volume("I A,1", "1900", "Aal", "Bethel")
        compare(VolumeType.SECOND_SERIES, volume.type)
        volume = Volume("S II", "1900", "Aal", "Bethel")
        compare(VolumeType.SUPPLEMENTS, volume.type)
        volume = Volume("R", "1900", "Aal", "Bethel")
        compare(VolumeType.REGISTER, volume.type)
        with self.assertRaises(ReDatenException):
            print(Volume("R I", "1900", "Aal", "Bethel").type)

    def test_sort_key(self):
        volume = Volume("I,1", "1900", "Aal", "Bethel")
        compare("1_01_1", volume.sort_key)
        volume = Volume("IX A,2", "1900", "Aal", "Bethel")
        compare("2_09_2", volume.sort_key)
        volume = Volume("X A", "1900", "Aal", "Bethel")
        compare("2_10_0", volume.sort_key)
        volume = Volume("S IV", "1900", "Aal", "Bethel")
        compare("3_04", volume.sort_key)
        volume = Volume("R", "1900", "Aal", "Bethel")
        compare("4", volume.sort_key)


class TestVolumes(TestCase):
    def setUp(self):
        self.re_volumes = Volumes()

    def test_len(self):
        self.assertEqual(84, len(self.re_volumes))

    def test_iter(self):
        iterator = iter(self.re_volumes)
        self.assertEqual("I,1", iterator.__next__())
        for i in range(0, 47):
            iterator.__next__()
        self.assertEqual("XXIV", iterator.__next__())
        self.assertEqual("I A,1", iterator.__next__())
        for i in range(0, 17):
            iterator.__next__()
        self.assertEqual("X A", iterator.__next__())
        self.assertEqual("S I", iterator.__next__())
        for i in range(0, 13):
            iterator.__next__()
        self.assertEqual("S XV", iterator.__next__())
        self.assertEqual("R", iterator.__next__())

    def test_iter_first_series(self):
        counter = 0
        for volume in self.re_volumes.first_series:
            compare(VolumeType.FIRST_SERIES, volume.type)
            counter += 1
        compare(49, counter)

    def test_iter_second_series(self):
        counter = 0
        for volume in self.re_volumes.second_series:
            compare(VolumeType.SECOND_SERIES, volume.type)
            counter += 1
        compare(19, counter)

    def test_iter_supplements(self):
        counter = 0
        for volume in self.re_volumes.supplements:
            compare(VolumeType.SUPPLEMENTS, volume.type)
            counter += 1
        compare(15, counter)

    def test_iter_register(self):
        counter = 0
        for volume in self.re_volumes.register:
            compare(VolumeType.REGISTER, volume.type)
            counter += 1
        compare(1, counter)

    def test_iter_all_volumes(self):
        counter = 0
        current_type = VolumeType.FIRST_SERIES
        following_types = [VolumeType.SECOND_SERIES,
                           VolumeType.SUPPLEMENTS,
                           VolumeType.REGISTER]
        for volume in self.re_volumes.all_volumes:
            compare(Volume, type(volume))
            if volume.type == current_type:
                pass
            elif volume.type == following_types[0]:
                current_type = following_types[0]
                del following_types[0]
            else:  # pragma: no cover
                raise TypeError("The types hasn't the right order. This section should never reached")
            counter += 1
        compare(84, counter)

    def test_get(self):
        with self.assertRaises(ReDatenException):
            print(self.re_volumes["tada"])
        with self.assertRaises(ReDatenException):
            print(self.re_volumes[1])
        compare("I,1", self.re_volumes["I,1"].name)
