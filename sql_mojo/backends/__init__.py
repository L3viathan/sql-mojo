import os
import inspect
import itertools
import importlib.util
from pathlib import Path
from abc import ABC


class BaseBackend(ABC):
    @classmethod
    def __subclasshook__(cls, C):
        if cls is BaseBackend:
            if hasattr(C, "query") and hasattr(C, "name"):
                return True
        return NotImplemented


class DummyBackend:
    def __init__(self, url):
        self.url = url
        self.name = "Dummy"

    def get_tables(self):
        return "foo bar bat".split()

    def query(self, data):
        return data

    @staticmethod
    def detect(url):
        return url.lower() == "dummy"


directories = [Path(os.path.realpath(__file__)).parent]
backends = {"dummy": DummyBackend}

for file in itertools.chain.from_iterable(
    folder.glob("*.py") for folder in directories
):
    if "__init__" in str(file):
        continue
    spec = importlib.util.spec_from_file_location(file.stem, str(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseBackend):
            backends[obj.name] = obj


def load(type_, url):
    if type_ in backends:
        return backends[type_](url)
    for backend in backends.values():
        if not hasattr(backend, "detect"):
            continue
        if backend.detect(url):
            return backend(url)
    raise ValueError(
        "Can't determine backend from URL, must specify with --type",
    )


def list():
    print("Available backends:")
    for name in backends:
        print(name)
