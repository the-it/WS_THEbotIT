from service.ws_re.template.re_page_abstract import RePageAbstract


class RePageComplex(RePageAbstract):
    @property
    def is_writable(self) -> bool:
        return False
