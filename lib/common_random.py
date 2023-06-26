# this file provides wrapper functions for random library so that wherever random is used through this library, stuff like seed etc remains consistent.
import importlib

class CommonRandom:
    def __init__(self, seed_val) -> None:
        self.randomlib = importlib.import_module("random", package=None)
        self.randomlib.seed(seed_val)

    def uniform(self, a, b):
        return self.randomlib.uniform(a, b)
    
    def randint(self, a, b):
        return self.randomlib.randint(a, b)
    
    def choice(self, options):
        return self.randomlib.choice(options)