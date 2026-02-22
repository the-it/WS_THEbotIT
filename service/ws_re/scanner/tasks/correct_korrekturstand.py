from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article


class COKSTask(ReScannerTask):
    """
    COrrect KorrekturStand

    This task corrects the Korrekturstand values:
    - "Platzhalter" -> "unvollständig"
    - "Fertig" -> "fertig"
    - "Korrigiert" -> "korrigiert"
    - "Unkorrigiert" -> "unkorrigiert"
    - "Unvollständig" -> "unvollständig"
    """

    def task(self):
        for article in self.re_page:
            if isinstance(article, Article):
                korrekturstand = article["KORREKTURSTAND"].value
                if korrekturstand:
                    if korrekturstand == "Platzhalter":
                        article["KORREKTURSTAND"].value = "unvollständig"
                    elif korrekturstand == "Fertig":
                        article["KORREKTURSTAND"].value = "fertig"
                    elif korrekturstand == "Korrigiert":
                        article["KORREKTURSTAND"].value = "korrigiert"
                    elif korrekturstand == "Unkorrigiert":
                        article["KORREKTURSTAND"].value = "unkorrigiert"
                    elif korrekturstand == "Unvollständig":
                        article["KORREKTURSTAND"].value = "unvollständig"
        return True
