import re

import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.api.wrapper import mipow
from resources.lib.util import MAX_BULBS, createListItem


def scan():

    addon = xbmcaddon.Addon()

    progress = xbmcgui.DialogProgressBG()
    progress.create(heading=addon.getLocalizedString(32001),
                    message=addon.getLocalizedString(32003))

    def callback(message: str) -> None:

        m = re.match(" *([0-9]+) bluetooth devices seen.*", message)
        if m:
            found = int(m.groups()[0])
            progress.update(message=addon.getLocalizedString(32004) %
                            found, percent=min(100, int(found * 3.4)))

    def _createListItem(s: str) -> xbmcgui.ListItem:

        xbmc.log(s, xbmc.LOGINFO)
        m = re.match("^([0-9A-F:]+) + (.+)$", s)
        return createListItem(label=m.groups()[1], label2=m.groups()[0], icon="bulb")

    try:
        bulbsStr = mipow(args=["--scan"], callback=callback)
        progress.update(message=addon.getLocalizedString(32005) %
                        len(bulbsStr), percent=100)

    finally:
        progress.close()

    if not bulbsStr:
        xbmcgui.Dialog().ok(heading=addon.getLocalizedString(
            32001), message=addon.getLocalizedString(32007))

    else:
        options: 'list[xbmcgui.ListItem]' = [
            _createListItem(s) for s in bulbsStr[1:]]
        selection = xbmcgui.Dialog().multiselect(heading=addon.getLocalizedString(32006),
                                                 options=options, useDetails=True, preselect=[i for i in range(len(options))])

        if not selection:
            return

        for i in range(min(len(selection), MAX_BULBS)):
            addon.setSetting(
                f"bulb_{i}_mac", options[selection[i]].getLabel2())
            addon.setSetting(f"bulb_{i}_name",
                             options[selection[i]].getLabel())
            addon.setSettingBool(f"bulb_{i}_enable", True)
            addon.setSetting(f"bulb_{i}_icon", "bulb")
            addon.setSettingBool(f"bulb_{i}_preselect", False)
            addon.setSettingInt(f"bulb_{i}_order", 1)

        for i in range(len(selection), MAX_BULBS):
            addon.setSetting(f"bulb_{i}_mac", "")
            addon.setSetting(f"bulb_{i}_name", "")
            addon.setSettingBool(f"bulb_{i}_enable", False)
            addon.setSetting(f"bulb_{i}_icon", "bulb")
            addon.setSettingBool(f"bulb_{i}_preselect", False)
            addon.setSettingInt(f"bulb_{i}_order", 1)
