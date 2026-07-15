from service.ws_re.scanner.tasks.base_task import ReScannerTask


class NAUETask(ReScannerTask):
    def task(self):
        for idx, article_list in enumerate(self.re_page.splitted_article_list):
            article = article_list.daten
            # first article is the main article, everything after it is a Nachtrag,
            # only the first Nachtrag bears the heading
            article["NACHTRAG"].value = idx > 0
            article["ÜBERSCHRIFT"].value = idx == 1
