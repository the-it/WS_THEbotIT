from service.ws_re.scanner.tasks.base_task import ReScannerTask
from tools import save_if_changed, add_category


class CARETask(ReScannerTask):
    def task(self) -> bool:
        for redirect in self.re_page.get_redirects():
            save_if_changed(page=redirect,
                            text=add_category(redirect.text, "RE:Redirect"),
                            change_msg="füge Kategorie für RE:Redirect ein.")
        return True
