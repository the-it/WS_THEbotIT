import re
import pywikibot

def frame_year(year):
    if int(year.group(0)) > 1945:
        return "'''" + year.group(0) + "'''"
    else:
        return year.group(0)

wiki = pywikibot.Site()
page = pywikibot.Page(wiki, "Paulys Realencyclopädie der classischen Altertumswissenschaft/Autoren")
raw = page.text

finding = re.findall("\|-\n\|(.*)\n\|(.*)", raw)
newstring = []

for item in finding:
    newstring.append("* ")
    newstring.append(item[0])
    newstring.append(" ")
    newstring.append(item[1])
    newstring.append("\n")
raw_list = "".join(newstring)
fit = re.compile("\d{4}")
temp = fit.sub(lambda x: frame_year(x), raw_list)
page = pywikibot.Page(wiki, "Benutzer:THE IT/re author")
page.text = '<div style="-moz-column-count:10; -webkit-column-count:10; column-count:10; -moz-column-width: 250px; -webkit-column-width:250px; column-width:250px;">\n' + temp + "</div>"
page.save()