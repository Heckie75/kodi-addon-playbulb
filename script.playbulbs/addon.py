import sys

from resources.lib.scanner import scan
from resources.lib.playbulb import Playbulb

if __name__ == "__main__":

    args = sys.argv
    if len(args) == 2 and args[1] == "scan":

        scan()

    else:
        playbulb = Playbulb()
        playbulb.play()
