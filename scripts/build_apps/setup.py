from distutils.core import setup
import py2exe
import pywikibot

setup(console=['160510_Fkraus_Schutz.py'], options={"py2exe": {"includes": ["Page", "Catscan"]}})
