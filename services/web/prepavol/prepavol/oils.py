from .file_reader import FileReader


class Avgas:
    def __init__(
        self,
        oil
    ) -> None:
        oils = Avgas.load_oil_data()
        if oil not in oils.keys():
            raise Exception(
                f"No such oil name. Valid oil names are {', '.join(oils.keys())}"
            )
        selected_oil = oils[oil]
        self.title: str = selected_oil["title"]
        self.density: float = selected_oil["density"]

    @staticmethod
    def load_oil_data():
        return FileReader("data/oil.yaml").readfile()