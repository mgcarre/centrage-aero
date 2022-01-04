import pkgutil

import yaml


class FileReader:
    def __init__(self, filename) -> None:
        self.filename = filename

    def readfile(self):
        stream = pkgutil.get_data(__name__, self.filename)
        if stream is None:
            raise Exception("YAML File cannot be read")
        return yaml.safe_load(stream)