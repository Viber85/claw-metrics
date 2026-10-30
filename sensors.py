"""Compatibility CLI; live HUD values are produced by the Decky backend."""
from main import battery_draw as draw

if __name__ == '__main__':
    print(draw())
