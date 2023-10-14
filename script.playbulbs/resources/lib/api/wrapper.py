import json
import os
import sys
import subprocess

import xbmc
from resources.lib.util import getAddonDir


def mipow(args: 'list[str]', callback=None) -> 'list[str]':

    addon_dir = getAddonDir()
    args_: 'list[str]' = list()

    if sys.platform == "win32":
         args_.append("python")
    else:
         args_.append("python3")

    args_.append(os.path.join(addon_dir, "resources", "lib", "api", "mipow.py"))
    args_.extend(args)

    xbmc.log(" ".join(args_), xbmc.LOGINFO)

    with subprocess.Popen(args=args_, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=(sys.platform == "win32")) as p:

        if callback:
            for line in p.stderr:
                callback(line)

        return [line.rstrip("\n") for line in iter(p.stdout.readlines())]


def requestSatus(macs: 'list[str]', callback=None) -> dict:

    args = [m for m in macs]
    args.extend(["--log", "INFO", "--color", "--effect", "--timer", "--security", "--name", "--json"])
    s = mipow(args=args, callback=callback)
    return json.loads("".join(s))
