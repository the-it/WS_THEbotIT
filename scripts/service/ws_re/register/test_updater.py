from testfixtures import compare

from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.base import RegisterException
from scripts.service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from scripts.service.ws_re.register.updater import Updater
from scripts.service.ws_re.register.volume import VolumeRegister
from scripts.service.ws_re.volumes import Volumes


class TestRegister(BaseTestRegister):
    def test_update_lemma(self):
        copy_tst_data("I_1_base", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "Aal", "redirect": True}
        with Updater(register) as updater:
            updater.update_lemma(update_dict, ["next"])
        post_lemma = register.get_lemma_by_name("Aal")
        self.assertTrue(post_lemma["redirect"])
        self.assertIsNone(post_lemma["next"])

    def test_update_lemma_by_sortkey(self):
        copy_tst_data("I_1_base", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "Äal", "redirect": True, "sort_key": "Aal", "next": "Aarassos"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("Äal")
        compare(True, post_lemma["redirect"])
        compare("Aal", post_lemma["sort_key"])
        post_lemma_next = register.get_lemma_by_name("Aarassos")
        compare("Äal", post_lemma_next["previous"])

    def test_update_lemma_by_sortkey_pre_and_post(self):
        copy_tst_data("I_1_base", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "Äarassos", "sort_key": "Aarassos", "previous": "Aal", "next": "Aba 1"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("Äarassos")
        compare("Aarassos", post_lemma["sort_key"])
        post_lemma_previous = register.get_lemma_by_name("Aal")
        compare("Äarassos", post_lemma_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Aba 1")
        compare("Äarassos", post_lemma_next["previous"])

    def test_update_lemma_by_sortkey_pre_and_next_lemma_other_name(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "Ö", "sort_key": "O", "previous": "Ä", "next": "Ü"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("Ö")
        compare("O", post_lemma["sort_key"])
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("Ö", post_lemma_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ü")
        compare("Ö", post_lemma_next["previous"])
        post_lemma_start = register.get_lemma_by_name("Vor A")
        compare("Ä", post_lemma_start["next"])
        post_lemma_end = register.get_lemma_by_name("D")
        compare("Ü", post_lemma_end["previous"])

    def test_update_by_sortkey_raise_error(self):
        copy_tst_data("I_1_update_previous_wrong", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "Äarassos", "previous": "Aal", "next": "Aba 1", "sort_key": "Aarassos"}
        with self.assertRaisesRegex(RegisterException, "!= next lemma name \"Ab 1\""):
            register.update_lemma(update_dict, [])
        previous_lemma = register.get_lemma_by_name("Aal")
        compare("Aarassos", previous_lemma["next"])
        next_lemma = register.get_lemma_by_name("Ab 1")
        compare("Aarassos", next_lemma["previous"])

    def test_update_by_sortkey_raise_error_missing_key(self):
        copy_tst_data("I_1_base", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "Äarassos", "sort_key": "Aarassos"}
        with self.assertRaisesRegex(RegisterException, "!= previous lemma name \"Aal\""):
            register.update_lemma(update_dict, [])
        previous_lemma = register.get_lemma_by_name("Aal")
        compare("Aarassos", previous_lemma["next"])
        next_lemma = register.get_lemma_by_name("Aba 1")
        compare("Aarassos", next_lemma["previous"])
        update_dict = {"lemma": "Äarassos", "sort_key": "Aarassos", "previous": "Aal"}
        with self.assertRaisesRegex(RegisterException, "!= next lemma name \"Aba 1\""):
            register.update_lemma(update_dict, [])
        previous_lemma = register.get_lemma_by_name("Aal")
        compare("Aarassos", previous_lemma["next"])
        next_lemma = register.get_lemma_by_name("Aba 1")
        compare("Aarassos", next_lemma["previous"])

    def test_update_no_update_possible(self):
        copy_tst_data("I_1_base", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "bubum", "redirect": True, "sort_key": "babam", "previous": "rubbish", "next": "something"}
        with self.assertRaisesRegex(RegisterException, "No strategy available"):
            register.update_lemma(update_dict, [])

    def test_update_next_and_previous(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "O", "previous": "Ä", "next": "Ü"}
        register._try_update_next_and_previous(update_dict, register.get_lemma_by_name("O"))
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("O", post_lemma_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ü")
        compare("O", post_lemma_next["previous"])

    def test_update_next_and_previous_in_normal_update(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "O", "previous": "Ä", "next": "Ü"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("O")
        compare("Ä", post_lemma["previous"])
        compare("Ü", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("O", post_lemma_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ü")
        compare("O", post_lemma_next["previous"])

    def test_update_next_and_previous_in_update_by_sortkey(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "Ö", "previous": "Ä", "next": "Ü"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("Ö")
        compare("Ä", post_lemma["previous"])
        compare("Ü", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("Ö", post_lemma_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ü")
        compare("Ö", post_lemma_next["previous"])

    def test_update_by_insert(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "B", "previous": "Ä", "next": "Ö"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("B")
        compare("Ä", post_lemma["previous"])
        compare("Ö", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("B", post_lemma_previous["next"])
        post_lemma_previous_previous = register.get_lemma_by_name("Vor A")
        compare("Ä", post_lemma_previous_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ö")
        compare("B", post_lemma_next["previous"])
        post_lemma_next_next = register.get_lemma_by_name("U")
        compare("Ö", post_lemma_next_next["previous"])

    def test_update_by_replace(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "B", "previous": "Ä", "next": "Ü"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("B")
        compare("Ä", post_lemma["previous"])
        compare("Ü", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("B", post_lemma_previous["next"])
        post_lemma_previous_previous = register.get_lemma_by_name("Vor A")
        compare("Ä", post_lemma_previous_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ü")
        compare("B", post_lemma_next["previous"])
        post_lemma_next_next = register.get_lemma_by_name("D")
        compare("Ü", post_lemma_next_next["previous"])

    def test_update_by_insert_after_previous(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "B", "previous": "Ä", "next": "Something"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("B")
        compare("Ä", post_lemma["previous"])
        compare(None, post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("B", post_lemma_previous["next"])
        post_lemma_previous_previous = register.get_lemma_by_name("Vor A")
        compare("Ä", post_lemma_previous_previous["next"])
        post_lemma_next = register.get_lemma_by_name("O")
        compare(None, post_lemma_next["previous"])

    def test_update_by_insert_no_next_exists(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "B", "previous": "Ä"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("B")
        compare("Ä", post_lemma["previous"])
        compare(None, post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("B", post_lemma_previous["next"])
        post_lemma_previous_previous = register.get_lemma_by_name("Vor A")
        compare("Ä", post_lemma_previous_previous["next"])
        post_lemma_next = register.get_lemma_by_name("O")
        compare(None, post_lemma_next["previous"])

    def test_update_by_insert_before_next(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "B", "previous": "Something", "next": "Ö"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("B")
        compare(None, post_lemma["previous"])
        compare("Ö", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("A")
        compare(None, post_lemma_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ö")
        compare("B", post_lemma_next["previous"])
        post_lemma_next_next = register.get_lemma_by_name("U")
        compare("Ö", post_lemma_next_next["previous"])

    def test_update_by_insert_before_next_no_previous(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "B", "next": "Ö"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("B")
        compare(None, post_lemma["previous"])
        compare("Ö", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("A")
        compare(None, post_lemma_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ö")
        compare("B", post_lemma_next["previous"])
        post_lemma_next_next = register.get_lemma_by_name("U")
        compare("Ö", post_lemma_next_next["previous"])

    def test_update_create_next_previous_supplement_by_sort_key(self):
        copy_tst_data("I_1_sorting2", "S I")
        register = VolumeRegister(Volumes()["S I"], Authors())
        update_dict = {"lemma": "Ö", "previous": "N", "next": "P"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("Ö")
        compare("N", post_lemma["previous"])
        compare("P", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("N")
        compare("Ö", post_lemma_previous["next"])
        post_lemma_previous_previous = register.get_lemma_by_name("A")
        compare(None, post_lemma_previous_previous["next"])
        post_lemma_next = register.get_lemma_by_name("P")
        compare("Ö", post_lemma_next["previous"])
        post_lemma_next_next = register.get_lemma_by_name("U")
        compare(None, post_lemma_next_next["previous"])
        self.assertTrue(register.get_index_of_lemma("A") <
                        register.get_index_of_lemma("N") <
                        register.get_index_of_lemma("Ö") <
                        register.get_index_of_lemma("P") <
                        register.get_index_of_lemma("U"))

    def test_update_create_next_previous_supplement_by_name(self):
        copy_tst_data("I_1_sorting2", "R")
        register = VolumeRegister(Volumes()["R"], Authors())
        update_dict = {"lemma": "O", "previous": "N", "next": "P"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("O")
        compare("N", post_lemma["previous"])
        compare("P", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("N")
        compare("O", post_lemma_previous["next"])
        post_lemma_previous_previous = register.get_lemma_by_name("A")
        compare(None, post_lemma_previous_previous["next"])
        post_lemma_next = register.get_lemma_by_name("P")
        compare("O", post_lemma_next["previous"])
        post_lemma_next_next = register.get_lemma_by_name("U")
        compare(None, post_lemma_next_next["previous"])
        self.assertTrue(register.get_index_of_lemma("A") <
                        register.get_index_of_lemma("N") <
                        register.get_index_of_lemma("O") <
                        register.get_index_of_lemma("P") <
                        register.get_index_of_lemma("U"))

    def test_update_create_next_previous_supplement_by_name_pre_exists(self):
        copy_tst_data("I_1_sorting2", "S I")
        register = VolumeRegister(Volumes()["S I"], Authors())
        update_dict = {"lemma": "O", "previous": "Ä", "next": "P"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("O")
        compare("Ä", post_lemma["previous"])
        compare("P", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("Ä")
        compare("O", post_lemma_previous["next"])
        post_lemma_previous_previous = register.get_lemma_by_name("Vor A")
        compare("Ä", post_lemma_previous_previous["next"])
        post_lemma_next = register.get_lemma_by_name("P")
        compare("O", post_lemma_next["previous"])
        post_lemma_next_next = register.get_lemma_by_name("U")
        compare(None, post_lemma_next_next["previous"])
        self.assertTrue(register.get_index_of_lemma("Vor A") <
                        register.get_index_of_lemma("Ä") <
                        register.get_index_of_lemma("O") <
                        register.get_index_of_lemma("P") <
                        register.get_index_of_lemma("U"))

    def test_update_create_next_previous_supplement_by_name_next_exists(self):
        copy_tst_data("I_1_sorting2", "R")
        register = VolumeRegister(Volumes()["R"], Authors())
        update_dict = {"lemma": "O", "previous": "N", "next": "Ü"}
        register.update_lemma(update_dict, [])
        post_lemma = register.get_lemma_by_name("O")
        compare("N", post_lemma["previous"])
        compare("Ü", post_lemma["next"])
        post_lemma_previous = register.get_lemma_by_name("N")
        compare("O", post_lemma_previous["next"])
        post_lemma_previous_previous = register.get_lemma_by_name("A")
        compare(None, post_lemma_previous_previous["next"])
        post_lemma_next = register.get_lemma_by_name("Ü")
        compare("O", post_lemma_next["previous"])
        post_lemma_next_next = register.get_lemma_by_name("D")
        compare("Ü", post_lemma_next_next["previous"])
        self.assertTrue(register.get_index_of_lemma("A") <
                        register.get_index_of_lemma("N") <
                        register.get_index_of_lemma("O") <
                        register.get_index_of_lemma("Ü") <
                        register.get_index_of_lemma("D"))

    def test_update_pre_and_next_not_possible(self):
        copy_tst_data("I_1_sorting2", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        update_dict = {"lemma": "B", "previous": "A", "next": "D"}
        with self.assertRaisesRegex(RegisterException, "Diff between previous and next aren't 1 or 2"):
            register.update_lemma(update_dict, [])
