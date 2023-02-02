import numpy as np

class Datum:
    def __init__(self, img, grid):
        self.img = img
        self.grid = grid.T # PMEL gives a transposed grid, fixed here.