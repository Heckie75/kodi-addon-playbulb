import xbmc
import xbmcaddon
import xbmcvfs
import os
import xbmcgui

MAX_BULBS = 10

_COLORS = ["off", "blue", "green", "cyan", "red", "magenta", "yellow", "white", "on"]

def getAddonDir() -> str:

    return xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))


def getIconPath(icon: str) -> str:

    return os.path.join(getAddonDir(), "resources", "assets", f"icon_{icon}.png")


def createListItem(label: str, label2: str, icon: str, rank: int = 0, preselect=False, notification: str = None, command: 'list[str]' = None, steps: int = 0) -> xbmcgui.ListItem:

    li = xbmcgui.ListItem(label=label, label2=label2)
    li.setArt({"thumb": getIconPath(icon=icon)})
    li.setProperty("rank", str(rank))
    li.setProperty("preselect", str(preselect))
    if notification:
        li.setProperty("notification", notification)
    if command:
        li.setProperty("command", "|".join(command))
    li.setProperty("steps", str(steps))
    return li


def getLightName(color: dict) -> 'tuple[str, str, bool]':

    _color = (color["white"], color["red"], color["green"], color["blue"])

    if _color == (0, 0, 0, 0):
        return xbmcaddon.Addon().getLocalizedString(32121), "off", True
    elif _color[0] > 0:
        return f"{xbmcaddon.Addon().getLocalizedString(32129)} ({int(100 * _color[0]/255)})%", "on", True

    v = 0
    max_ = 0
    min_ = 255
    for i in range(1, 4):
        c = _color[4 - i]
        if c:
            v += 1 << (i - 1)
            min_ = min(c, min_)
            max_ = max(c, max_)

    return f"{xbmcaddon.Addon().getLocalizedString(32121 + v)} ({int(100 * max_/255)}%)", _COLORS[v],  v and 0.8 < (max_ / min_) < 1.2
