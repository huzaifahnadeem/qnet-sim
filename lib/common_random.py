import importlib

class CommonRandom:
    def __init__(self, seed_val) -> None:
        self.randomlib = importlib.import_module("random", package=None)
        self.randomlib.seed(seed_val)

    def uniform(self, a, b):
        return self.randomlib.uniform(a, b)