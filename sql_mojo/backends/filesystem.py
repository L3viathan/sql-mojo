from pathlib import Path

class FileSystemBackend:
    name = "fs"

    def __init__(self, basepath):
        self.basepath = Path(basepath).expanduser().absolute()
        self.name = f"file:///{self.basepath}"
        self.fieldgetter = {
            "name": lambda x: x.name,
            "ctime": lambda x: x.stat().st_ctime,
            "mtime": lambda x: x.stat().st_mtime,
            "atime": lambda x: x.stat().st_atime,
            "owner": lambda x: x.owner(),
            "group": lambda x: x.group(),
            "permissions": lambda x: int(oct(x.stat().st_mode)[-3:]),
            "size": lambda x: self.human_readable(x.stat().st_size),
        }

    def get_tables(self):
        return [
            f'"{element.relative_to(self.basepath)}"'
            for element in self.basepath.iterdir()
        ]

    @staticmethod
    def human_readable(size):
        for unit in ["", "K", "M", "G", "T", "P"]:
            if size < 1024:
                return f"{size:3.1f}{unit}" if unit else f"{size}"
            size /= 1024
        return f"{size:3.1f}E"

    def query(self, data):
        if any(item["type"] == "star" for item in data["columns"]):
            fields = [*self.fieldgetter.keys()]
        else:
            fields = [item["value"] for item in data["columns"]]
        assert not set(fields) - set(self.fieldgetter)
        index = data["table"]["value"]
        if index == "*":
            index = ""
        path = self.basepath / index
        if path.is_dir():
            files = list(path.iterdir())
        elif "*" in index:
            files = list(self.basepath.glob(index))
        else:
            files = [path]
        return [
            {field: self.fieldgetter[field](file) for field in fields} for file in files
        ]

    @staticmethod
    def detect(url):
        if ":" in url:
            return False
        return Path(url).exists()
