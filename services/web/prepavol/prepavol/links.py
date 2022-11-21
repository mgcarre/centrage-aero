from .file_reader import FileReader

class Links:
    def __init__(
        self
        ) -> None:
        self.links = self.load_data()

    @staticmethod
    def load_data():
        return FileReader("data/kiosk_links.yaml").readfile()