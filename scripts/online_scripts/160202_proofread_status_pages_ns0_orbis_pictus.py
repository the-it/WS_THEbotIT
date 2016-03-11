# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import requests
import pywikibot
from pywikibot import proofreadpage

titles = ["I. Deus – Gott",
"II. Mundus – Die Welt",
"III. Coelum – Der Himmel",
"IV. Ignis – Das Feuer",
"V. Aër – Die Lufft",
"VI. Aqua – Das Wasser",
"VII. Nubes – Die Wolcken",
"VIII. Terra – Die Erde",
"IX. Terrae-Foetûs – Erdgewächse",
"X. Metalla – Die Metalle",
"XI. Lapides – Die Steine",
"XII. Arbor – Der Baum",
"XIII. Fructûs Arborum – Die Baumfruochte",
"XIV. Flores – Die Blumen",
"XV. Olera – Gartenfrüchte",
"XVI. Fruges – Geträid oder Feld-Früchte",
"XVII. Frutices – Die Sträuche oder Stauden",
"XVIII. Animalia et primùm Aves – Die Thiere und erstlich Die Vögel",
"XIX. Aves domesticae – Haus-Geflügel",
"XX. Oscines – Gesang-Vögel",
"XXI. Aves Compestres et Sylvestres – Feld- und Wald-Geflügel",
"XXII. Aves Rapaces – Raub-Vögel",
"XXIII. Aves Aquaticae – Wasser-Geflügel",
"XXIV. Insecta volantia – Fliegend Ungeziefer",
"XXV. Quadrupedia et primùm Domestica – Vierfüssigte Thiere und erstlich Die Haus-Thiere",
"XXVI. Pécora – Herd-Vieh",
"XXVII. Jumenta – Last-Vieh",
"XXVIII. Ferae Pécudes – Wild-Vieh",
"XXIX. Ferae Bestiae – Wilde Thiere",
"XXX. Serpentes et Reptilia – Schlangen und Gewürme",
"XXXI. Insecta repentia – Kriechend Ungezifer",
"XXXII. Amphibia – Beydlebige Thiere",
"XXXIII. Pisces Fluviatiles et Lacustres – Fluß- und Weiher-Fische",
"XXXIV. Marini Pisces et Conchae – Meerfische und Muscheln",
"XXXV. Homo – Der Mensch",
"XXXVI. Septem Aetates Hominis – Die Sieben Alter des Menschen",
"XXXVII. Membra Hominis Externa – Die äusserlichen Glieder des Menschen",
"XXXVIII. Caput et Manûs – Haupt und Hände",
"XXXIX. Caro et Viscera – Fleisch und Ingeweid",
"XL. Canales et Ossa – Das Geäder und Gebeine",
"XLI. Sensûs externi et interni – Euserliche und innerliche Sinnen",
"XLII. Anima Hominis – Die Seele des Menschen",
"XLIII. Deformes et Monstrosi – Ungestalte und Mißgeburten",
"XLIV. Hortorum Cultura – Die Gärtnerey",
"XLV. Agricultura – Der Feldbau",
"XLVI. Pecuaria – Die Viehzucht",
"XLVII. Mellificium – Der Honig-Bau",
"XLVIII. Molitura – Das Mühlwerk",
"XLIX. Panificium – Die Brodback",
"L. Piscatio – Die Fischerey",
"LI. Aucupium – Der Vogelfang",
"LII. Venatus – Die Jagt",
"LIII. Lanionia – Die Fleischhack",
"LIV. Coquinaria – Das Kochwerk",
"LV. Vindemia – Die Weinlese",
"LVI. Zythopoeia – Die Bierbraw",
"LVII. Convivium – Die Mahlzeit",
"LVIII. Tractatio Lini – Flachs-Arbeit",
"LIX. Textura – Das Gewebe",
"LX. Lintea – Die Leinwat",
"LXI. Sartor – Der Schneider",
"LXII. Sutor – Der Schuster",
"LXIII. Faber lignarius – Der Zimmermann",
"LXIV. Faber Murarius – Der Mäurer",
"LXV. Machinae – Gewerk-Zeug",
"LXVI. Domus – Das Haus",
"LXVII. Metallifodina – Die Erzgrube",
"LXVIII. Faber Ferrarius – Der Schmied",
"LXIX. Scriniarius et Tornator – Der Schreiner und Drechßler",
"LXX. Figulus – Der Döpfer",
"LXXI. Partes Domûs – Die Hausgemächer",
"LXXII. Hypocaustum, cum Dormitorio – Stube und Kammer",
"LXXIII. Putei – Schöpfbrunnen",
"LXXIV. Balneum – Das Bad",
"LXXV. Tonstrina – Die Barbierstube",
"LXXVI. Equile – Der Pferdstall",
"LXXVII. Horologia – Uhrwerke",
"LXXVIII. Pictura – Mahlerey",
"LXXIX. Specularia – Gesicht-Gläser",
"LXXX. Vietor – Der Böttcher",
"LXXXI. Restio et Lorarius – Der Seiler und Riemer",
"LXXXII. Viator – Der Wandersmann",
"LXXXIII. Eques – Der Reiter",
"LXXXIV. Vehicula – Die Wägen",
"LXXXV. Vectura – Das Fuhrwerk",
"LXXXVI. Transitus Aquarum – Die Uberfuhrt",
"LXXXVII. Natatus – Das Schwimmen",
"LXXXVIII. Navis actuaria – Das Ruderschiff",
"LXXXIX. Navis oneraria – Das Lastschiff",
"XC. Naufragium – Der Schiffbruch",
"XCI. Ars Scriptoria – Die Schreibkunst",
"XCII. Papyrus – Das Papier",
"XCIII. Typographia – Die Buchdruckerey",
"XCIV. Bibliopolium – Der Buchladen",
"XCV. Bibliopegus – Der Buchbinder",
"XCVI. Liber – Das Buch",
"XCVII. Schola – Die Schul",
"XCVIII. Muséum – Das Kunstzimmer",
"XCIX. Artes Sermonis – Red-Künste",
"C. Instrumenta Musica – Klangspiele",
"CI. Philosophia – Die Weltweißheit",
"CII. Geometria – Die Erdmeßkunst",
"CIII. Sphaera coelestis – Die Himmelskugel",
"CIV. Planetarum-Adspectûs – Planeten-Stellungen",
"CV. Phases Lunae – Des Monds Gestalten",
"CVI. Eclipses – ☉ und ☽ Finsternissen",
"CVII. Sphaera terrestris – Die Erdkugel",
"CVIII. Europa – Europa",
"CIX.Ethica – Die Sittenlehre",
"CX. Prudentia – Die Klugheit",
"CXI. Sedulitas – Die Aemsigkeit",
"CXII. Temperantia – Die Mässigkeit",
"CXIII. Fortitudo – Die Starkmütigkeit",
"CXIV. Patientia – Die Gedult",
"CXV. Humanitas – Die Leutseeligkeit",
"CXVI. Justitia – Die Gerechtigkeit",
"CXVII. Liberalitas – Die Mildigkeit",
"CXVIII. Societas Coniugalis – Der Ehestand",
"CXIX. Arbor Consanguinitatis – Der Sipschafft-Baum",
"CXX. Societas Parentalis – Der Eltern Stand",
"CXXI. Societas Herilis – Die Herrschafft",
"CXXII. Urbs – Die Stadt",
"CXXIII. Interiora Urbis – Das Inwendige der Stadt",
"CXXIV. Judicium – Das Gerichte",
"CXXV. Supplicia Maleficorum – Die Leibsstraffen der Ubelthäter",
"CXXVI. Mercatura – Die Kauffmanschafft",
"CXXVII. Mensurae et Pondera – Maß und Gewichte",
"CXXVIII. Ars Medica – Die Arzney-Kunst",
"CXXIX. Sepultura – Die Begräbnis",
"CXXX. Ludus Scenicus – Das Schauspiel",
"CXXXI. Praestigiae – Die Gaukeley",
"CXXXII. Palaestra – Die Fechtschul",
"CXXXIII. Ludus Pilae – Das Ballspiel",
"CXXXIV. Ludus Aleae – Das Bretspiel",
"CXXXV. Cursûs Certamina – Lauffspiele",
"CXXXVI. Ludi pueriles – Kinderspiele",
"CXXXVII. Regnum et regio – Das Reich und Die Landschafft",
"CXXXVIII. Regia Majestas – Die Königliche Majestät",
"CXXXIX. Miles – Der Kriegsmann",
"CXL. Castra – Das Feldlager",
"CXLI. Acies et Praelium – Die Schlachtordnung und Feldschlacht",
"CXLII. Pugna Navalis – Das See-Treffen",
"CXLIII. Obsidium Urbis – Die Stadt-Belägerung",
"CXLIV. Religio – Der Gottesdienst",
"CXLV. Gentilismus – Das Heidenthum",
"CXLVI. Judaismus – Das Judenthum",
"CXLVII. Christianismus – Das Christenthum",
"CXLVIII. Mahometismus – Der Mahometische Glaube",
"CXLIX. Providentia Dei – Die Vorsehung Gottes",
"CL. Judicium Extremum – Das Jüngste Gerichte"]

def add_zeros(number, digits):
    number_str = str(number)
    if number < 10:
        for members in range(digits-1):
            number_str = "0" + number_str
    elif number < 100:
        for members in range(digits-2):
            number_str = "0" + number_str
    elif number < 1000:
        for members in range(digits-3):
            number_str = "0" + number_str
    return number_str

site = pywikibot.Site()

for idx, i in enumerate(range(6, 297, 2)):
    page = pywikibot.Page(site, 'Orbis sensualium pictus/{}'.format(titles[idx]))
    print(i, titles[idx])

    first_page = proofreadpage.ProofreadPage(site, "Seite:OrbisPictus {}.jpg".format(add_zeros(i, 3)))
    second_page = proofreadpage.ProofreadPage(site, "Seite:OrbisPictus {}.jpg".format(add_zeros(i + 1, 3)))

    status_1 = first_page.status
    status_2 = second_page.status

    if status_1 == "Fertig" and status_2 == "Fertig":
        status = "Fertig"
    elif status_1 == "Unkorrigiert" or status_2 == "Unkorrigiert":
        status = "Unkorrigiert"
    else:
        status = "Korrigiert"

    print(status_1, status_2, status)
    tempstatus = re.search("(?:[Uu]nkorrigiert)|(?:[Kk]orrigiert)|(?:[Ff]ertig)|(?:[Uu]nvollständig)", page.text)
    print(tempstatus.group())
    if tempstatus.group() != status:
        temptext = re.sub("\|STATUS=(?:[Uu]nkorrigiert)|(?:[Kk]orrigiert)|(?:[Ff]ertig)|(?:[Uu]nvollständig)", "|STATUS={}".format(status), page.text)
        page.text = temptext
        page.save(summary= "automatische Setzung des Seitenstatus", botflag= True)