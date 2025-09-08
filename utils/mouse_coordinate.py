from pynput import *


def get_coords(x, y):
    print("Now at: {}".format((x, y)))


if __name__ == '__main__':
    with mouse.Listener(on_move=get_coords) as listen:
        listen.join()