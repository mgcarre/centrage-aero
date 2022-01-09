from .file_reader import FileReader


class Aeroclub():
    def __init__(self) -> None:
        clubs = Aeroclub.load_club_data()
        self.clubs = clubs

    @property
    def keys(self):
        keys = []
        for i in self.clubs:
            keys.append(i["title"])
        return keys

    def get_plane_keys(self, value):
        for i in self.clubs:
            if i["title"] == value:
                return i["planes"]

    @staticmethod
    def load_club_data():
        return FileReader("data/clubs.yaml").readfile()