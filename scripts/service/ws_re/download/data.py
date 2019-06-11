_ARCHIVES = {
    "Pauly Supp.rar": "PaulySupp",
    "Pauly-Wissowa_54-66.rar": "PaulyWissowa5466",
    "Pauly-Wissowa_41-53.rar": "PaulyWissowa4153_201412",
    "Pauly-Wissowa_31-40.rar": "PaulyWissowa3140_201412",
    "Pauly-Wissowa_21-30.rar": "PaulyWissowa2130",
    "Pauly-Wissowa_11-20.rar": "PaulyWissowa1120",
    "Pauly-Wissowa_1-10.rar": "PaulyWissowa110",
}

_RAW_FILES = {
    "PaulySupp": "Pauly Supp.rar",
    "PaulyWissowa5466": "Pauly-Wissowa_54-66.rar",
    "PaulyWissowa4153": "Pauly-Wissowa_41-53.rar",
    "PaulyWissowa3140": "Pauly-Wissowa_31-40.rar",
    "PaulyWissowa2130": "Pauly-Wissowa_21-30.rar",
    "PaulyWissowa1120": "Pauly-Wissowa_11-20.rar",
    "PaulyWissowa110": "Pauly-Wissowa_1-10.rar",
}

_MAPPINGS = {
    "I,1": {"source": ("PaulyWissowa110", "Aal Apollokrates"), "pages": ((-1, 10010, 10370),)},
    "I,2": {"source": ("PaulyWissowa110", "Aal Apollokrates"), "pages": ((1439, 10370, 10735),)},
    "II,1": {"source": ("PaulyWissowa110", "Apollon Artemis"), "pages": ((-1, 30002, 30362),)},
    "II,2": {"source": ("PaulyWissowa110", "Artemisia Barbaroi"), "pages": ((1439, 40004, 40359),)},
    "III,1": {"source": ("PaulyWissowa110", "Barbarus Campanus"), "pages": ((-1, 50002, 50362),)},
    "III,2": {"source": ("PaulyWissowa110", "Campanus ager Claudius"), "pages": ((1439, 60002, 60004),
                                                                                 (1451, 60006, 60370))},
    "IV,1": {"source": ("PaulyWissowa110", "Claudius mons Cornificius"), "pages": ((-1, 70002, 70410),)},
    "IV,2": {"source": ("PaulyWissowa110", "Corniscae Demodoros"), "pages": ((1631, 80002, 80312),)},
    "V,1": {"source": ("PaulyWissowa110", "Demogenes Ephoroi"), "pages": ((-1, 90002, 90385),)},
    "V,2": {"source": ("PaulyWissowa110", "Demogenes Ephoroi"), "pages": ((1531, 90385, 90718),)},
    "VI,1": {"source": ("PaulyWissowa110", "Ephoros-Eutychos"), "pages": ((-1, 2, 386),)},
    "VI,2": {"source": ("PaulyWissowa110", "Euxantios-Fornaces"), "pages": ((1535, 2, 337),)},
    "VII,1": {"source": ("PaulyWissowa1120", "Fornax-Glykon"), "pages": ((-1, 2, 370),)},
    "VII,2": {"source": ("PaulyWissowa1120", "Glykyrrh-Helikeia"), "pages": ((1471, 2, 354),)},
    "VIII,1": {"source": ("PaulyWissowa1120", "Helikon-Hestia"), "pages": ((-1, 2, 330),)},
    "VIII,2": {"source": ("PaulyWissowa1120", "Hestiaia Hyagnis"), "pages": ((1311, 160002, 160331),)},
    "IX,1": {"source": ("PaulyWissowa1120", "Hyaia Imperator"), "pages": ((-1, 170002, 170301),)},
    "IX,2": {"source": ("PaulyWissowa1120", "Imperium Iugum"), "pages": ((1199, 180002, 180358),)},
    "X,1": {"source": ("PaulyWissowa1120", "Iugurtha Ius Latii"), "pages": ((-1, 190002, 190322),)},
    "X,2": {"source": ("PaulyWissowa1120", "Ius liberorum Katochos"), "pages": ((1279, 200002, 200318),)},
    "XI,1": {"source": ("PaulyWissowa1120", "Katoikoi Komoedie"), "pages": ((-1, 210002, 210322),)},
    "XI,2": {"source": ("PaulyWissowa1120", "Komogrammateus Kynegoi"), "pages": ((1279, 220002, 220314),)},
    "XII,1": {"source": ("PaulyWissowa2130", "Kynesioi Legio"), "pages": ((-1, 230002, 230334),)},
    "XII,2": {"source": ("PaulyWissowa2130", "Legio Libanon"), "pages": ((1327, 240002, 240308),)},
    "XIII,1": {"source": ("PaulyWissowa2130", "Libanos Lokris"), "pages": ((-1, 250002, 250324),)},
    "XIII,2": {"source": ("PaulyWissowa2130", "Lokroi Lysimachides"), "pages": ((1287, 260002, 260320),)},
    "XIV,1": {"source": ("PaulyWissowa2130", "Lysimachos Mantike"), "pages": ((-1, 270002, 270324),)},
    "XIV,2": {"source": ("PaulyWissowa2130", "Mantikles Mazaion"), "pages": ((1287, 280002, 280326),)},
    "XV,1": {"source": ("PaulyWissowa2130", "Mazaios Mesyros"), "pages": ((-1, 290002, 290326),)},
    "XV,2": {"source": ("PaulyWissowa2130", "Met Molaris lapis"), "pages": ((1295, 300002, 300318),)},
    "XVI,1": {"source": ("PaulyWissowa2130", "Molatzes Myssi"), "pages": ((-1, 310002, 310303),)},
    "XVI,2": {"source": ("PaulyWissowa2130", "Mystagogos Nereae"), "pages": ((1207, 320002, 320338),)},
}

_MISSING_PAGES = (
    # Hyaia Imperator - IX,1
    170260, 170265, 170270, 170275, 170280, 170285, 170290, 170291, 170292, 170295,
)
