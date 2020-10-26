#!/usr/bin/python2
# -*- coding: utf-8 -*-

import json
import os
import re
import subprocess
import sys
import threading
import time
import urlparse

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

__PLUGIN_ID__ = "plugin.audio.playbulb"

SLOTS = 8
PRESETS = 8
BULB_ICONS = ["icon_lamp", "icon_globe", "icon_livingroom", "icon_bedroom",
                "icon_kitchen", "icon_bathroom", "icon_hall"]

reload(sys)
sys.setdefaultencoding('utf8')

settings = xbmcaddon.Addon(id=__PLUGIN_ID__)
addon_dir = xbmc.translatePath( settings.getAddonInfo('path') )

_light_names = ["off", "blue", "green", "cyan", "red", "magenta", "yellow", "white", "on"]
_menu = []




class ContinueLoop(Exception):
    pass




class BulbException(Exception):
    pass




def _exec_mipow(mac, params):

    if settings.getSetting("host") == "1":
        # remote over ssh
        call = ["ssh", settings.getSetting("host_ip"),
                "-p %s" % settings.getSetting("host_port"),
                settings.getSetting("host_path")]
        call += [ mac ] + params

    else:
        # local
        call = [addon_dir + os.sep + "lib" + os.sep + "mipow.exp"]
        call += [ mac ] + params

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    p = subprocess.Popen(call,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    out, err = p.communicate()
    xbmc.log(out, xbmc.LOGNOTICE)
    return out.decode("utf-8")




def _exec_bluetoothctl():

    macs = []
    names = []

    if settings.getSetting("host") == "1":
        # remote over ssh
        p2 = subprocess.Popen(["ssh", settings.getSetting("host_ip"),
                            "-p %s" % settings.getSetting("host_port"),
                            "echo -e 'devices\nquit\n\n' | bluetoothctl"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    else:
        # local
        p1 = subprocess.Popen(["echo", "-e", "devices\nquit\n\n"],
                                  stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["bluetoothctl"], stdin=p1.stdout,
                              stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        p1.stdout.close()

    out, err = p2.communicate()

    xbmc.log(out, xbmc.LOGNOTICE)

    for match in re.finditer('([0-9A-F:]+:AC:E6) (.+)',
                             out.decode("utf-8")):
        macs += [match.group(1)]
        names += [match.group(2)]

    return macs, names




def discover():

    inserts = []
    free = []

    macs, names = _exec_bluetoothctl()

    for m in range(len(macs)):
        try:
            for i in range(SLOTS):
                smac = settings.getSetting("dev_%i_mac" % i)
                senabled = settings.getSetting("dev_%i_enable" % i)
                if smac == macs[m]:
                    settings.setSetting("dev_%i_name" % i, names[m])
                    raise ContinueLoop

                elif (smac == "" or senabled == "false") and i not in free:
                    free += [ i ]


            inserts += [ m ]

        except ContinueLoop:
            continue

    if len(free) == 0 and len(inserts) > 0:
        xbmc.executebuiltin(
            "Notification(All slots are occupied, "
            "Disable a device from list!)")
        return

    for m in inserts:
        slot = None
        if len(free) > 0:
            slot = free.pop(0)
        else:
            continue

        settings.setSetting("dev_%i_mac" % slot, macs[m])
        settings.setSetting("dev_%i_name" % slot, names[m])

    if len(macs) == 0:
        xbmc.executebuiltin(
            "Notification(No Mipow Playbulbs found, "
            "Check if at least one bulb is paired!)")

    elif len(inserts) == 0:
        xbmc.executebuiltin(
            "Notification(No new bulbs found, "
            "Check already paired bulbs!)")
    else:
        xbmc.executebuiltin(
            "Notification(New playbulbs found, "
            "%i new bulbs added to device list)" % len(inserts))




def _get_directory_by_path(path):

    if path == "/":
        return _menu[0]

    tokens = path.split("/")[1:]
    directory = _menu[0]

    while len(tokens) > 0:
        path = tokens.pop(0)
        for node in directory["node"]:
            if node["path"] == path:
                directory = node
                break

    return directory




def _build_param_string(param, values, current = ""):

    if values == None:
        return current

    for v in values:
        current += "?" if len(current) == 0 else "&"
        current += param + "=" + str(v)

    return current




def _add_list_item(entry, path):

    if path == "/":
        path = ""

    item_path = path + "/" + entry["path"]
    item_id = item_path.replace("/", "_")

    param_string = ""
    if "send" in entry:
        param_string = _build_param_string(
            param = "send",
            values = entry["send"],
            current = param_string)

    if "param" in entry:
        param_string = _build_param_string(
            param = entry["param"][0],
            values = [ entry["param"][1] ],
            current = param_string)

    if "msg" in entry:
        param_string = _build_param_string(
            param = "msg",
            values = [ entry["msg"] ],
            current = param_string)

    if "node" in entry:
        is_folder = True
    else:
        is_folder = False

    label = entry["name"]
    if settings.getSetting("label%s" % item_id) != "":
        label = settings.getSetting("label%s" % item_id)

    if "icon" in entry:
        icon_file = os.path.join(addon_dir, "resources", "assets", entry["icon"] + ".png")
    else:
        icon_file = None

    li = xbmcgui.ListItem(label, iconImage=icon_file)

    xbmcplugin.addDirectoryItem(handle=addon_handle,
                            listitem=li,
                            url="plugin://" + __PLUGIN_ID__
                            + item_path
                            + param_string,
                            isFolder=is_folder)




def _get_macs_of_target(target):

    if not target.startswith("group_"):
        return [ target ]

    target = target.replace("group_", "")

    macs = []

    for i in range(SLOTS):

        mac = settings.getSetting("dev_%i_mac" % i)
        enabled = settings.getSetting("dev_%i_enabled" % i)
        groups = int(settings.getSetting("dev_%i_groups" % i))

        if mac == "" or enabled != "true":
            continue

        if target == "all":
            macs += [ mac ]
            continue

        group = pow(2, int(target))
        if (group & groups == group):
            macs += [ mac ]

    return macs




def _get_status(target):

    macs = _get_macs_of_target(target)

    output = _exec_mipow(macs[0], ["--color", "--effect", "--timer", "--random", "--json"])
    return json.loads(output)




def _get_light_name(color):

    if len(color) <> 4:
        return "off", True

    v = 0
    max = 0
    min = 255
    for i in range(4):
        c = int(color[i])
        v += 0 if c == 0 else pow(2, 3 - i)
        min = c if c > 0 and c < min else min
        max = c if c > max else max

    return _light_names[8 if v > 8 else v], min == max




def _active_timer(status):

    activeTimer = False
    for t in range(4):
        activeTimer = activeTimer or not status["timer"][t]["start"] == "n/a"

    return activeTimer




def _get_name_by_mac(mac):

    for i in range(SLOTS):
        if settings.getSetting("dev_%i_mac" % i) == mac:
            return settings.getSetting("dev_%i_name" % i)

    return mac




def _build_menu(target, status = None):

    if not status:
        status = _get_status(target)

    if target == "group_all":
        stext = "All bulbs: "
    elif target.startswith("group_"):
        stext = "%s: " % settings.getSetting(target)
    else:
        stext = "%s: " % _get_name_by_mac(target)

    if status["random"]["status"] == "running":
        stext = "Security mode is running until %s " % (status["random"]["stop"])
        sicon = "icon_random"
    elif status["state"]["effect"]["effect"] == "halt":
        name, exact = _get_light_name(status["state"]["color"][5:-1].split(","))
        stext += ("kind of " if not exact else "") + name
        sicon = "icon_bulb_%s" % name
    else:
        name, exact = _get_light_name(status["state"]["effect"]["color"][5:-1].split(","))
        stext += ("kind of " if not exact else "") + name

        stext = "Effect: "
        stext += status["state"]["effect"]["effect"]
        stext += ", " + ("some kind of " if not exact else "") + name
        stext += ", " + status["state"]["effect"]["time"]["speed_human"]
        sicon = "icon_" + status["state"]["effect"]["effect"]

    device = [
        {
            "path" : "info",
            "name" : stext,
            "icon" : sicon,
            "send" : ["--off"],
            "msg" : "Turn off"
        }
    ]

    if status["random"]["status"] == "running":
        device += [
            {
                "path" : "random_off",
                "name" : "Turn security mode off",
                "icon" : "icon_power",
                "send" : ["--random", "off"],
                "msg" : "Turn security mode off"
            }
        ]
    elif status["state"]["effect"]["effect"] <> "halt":
        device += [
            {
                "path" : "effect_halt",
                "name" : "Halt current effect, keep light",
                "icon" : "icon_halt",
                "send" : ["--halt"],
                "msg" : "Halt current effect by keeping light"
            }
        ]

    if status["state"]["color"] == "off":
        name, exact = _get_light_name(status["state"]["effect"]["color"][5:-1].split(","))
        device += [
            {
                "path" : "turn_on",
                "name" : "Turn light on",
                "icon" : "icon_bulb_on",
                "send" : ["--on"],
                "msg" : "Turn light on"
            },
            {
                "path" : "turn_on",
                "name" : "Toggle light",
                "icon" : "icon_bulb_%s" % name,
                "send" : ["--toggle"],
                "msg" : "Toggle light"
            }
        ]
    elif status["state"]["color"] <> "off":
        device += [
            {
                "path" : "turn_off",
                "name" : "Turn light off",
                "icon" : "icon_bulb_off",
                "send" : ["--off"],
                "msg" : "Turn light off"
            },
            {
                "path" : "turn_off",
                "name" : "Toggle light",
                "icon" : "icon_bulb_off",
                "send" : ["--off"],
                "msg" : "Toggle light"
            }
        ]

        if status["state"]["effect"]["effect"] == "halt":
            device += [
                {
                    "path" : "up",
                    "name" : "Turn up light",
                    "icon" : "icon_bulb_up",
                    "send" : ["--up"],
                    "msg" : "Turn up light"
                },
                {
                    "path" : "dim",
                    "name" : "Dim light",
                    "icon" : "icon_bulb_down",
                    "send" : ["--down"],
                    "msg" : "Dim light"
                }
            ]

    device += [
        {
            "path" : "light",
            "param" : [ "status", json.dumps(status)],
            "name" : "Set light...",
            "icon" : "icon_presets",
            "node" : _build_menu_color("--color")
        }
    ]

    device += [
        {
            "path" : "effect",
            "param" : [ "status", json.dumps(status)],
            "name" : "Run effect...",
            "icon" : "icon_effect",
            "node" : _build_menu_effects(status)
        }
    ]

    device += _build_active_timer_entries(status)

    activeTimer = _active_timer(status)
    another = "another " if activeTimer else ""

    device += [
        {
            "path" : "program",
            "param" : [ "status", json.dumps(status)],
            "name" : "Run %sprogram..." % another,
            "icon" : "icon_program",
            "node" : _build_menu_programs(status)
        }
    ]

    return device




def _build_menu_color(command, parameter=[], normalize = False):

    entries = []
    for i in range(PRESETS):
        if settings.getSetting("fav_%i_enabled" % i) == "true":
            name, exact = _get_light_name(settings.getSetting("fav_%i_color" % i).split("."))

            setting = settings.getSetting("fav_%i_color" % i).split(".")

            if normalize:
                for j in range(len(setting)):
                    setting[j] = 1 if setting[j] <> "0" else "0"

            entries += [
                {
                    "path" : "/" + command + ("%i" % i),
                    "name" : "%s" % settings.getSetting("fav_%i_name" % i),
                    "icon" : "icon_bulb_%s" % name,
                    "send" : [ command ] + setting + parameter,
                    "msg" : "Set light to %s" % settings.getSetting("fav_%i_name" % i)
                }
            ]

    return entries




def _build_menu_effects(status):

    entries = []

    for effect in ["rainbow", "candle", "pulse", "blink", "disco"]:
        if settings.getSetting("effect_%s_enabled" % effect) == "true":
            entries += [
                {
                    "path" : effect,
                    "name" : effect,
                    "icon" : "icon_%s" % effect,
                    "node" : _build_menu_effects_hold(effect)
                }
            ]

    if status["state"]["effect"]["effect"] <> "halt":
        entries += [
            {
                "path" : "effect_halt",
                "param" : [ "status", json.dumps(status)],
                "name" : "Halt current effect, keep light",
                "icon" : "icon_halt",
                "send" : ["--halt"],
                "msg" : "Halt current effect by keeping light"
            }
        ]

    return entries




def _build_menu_effects_hold(effect):

    entries = []
    unit = "bpm" if effect in ["blink", "disco"] else "sec"

    for i in range(5):
        setting = settings.getSetting("effect_%s_%s_%i" % (effect, unit, i))
        hold = 255
        if effect == "rainbow":
            hold = int(int(setting) * (255.0 / 390.0))
        elif effect == "pulse":
            hold = int(int(setting) * (255.0 / 130.0))
        elif effect == "blink":
            hold = int(3000.0 / float(setting))
        elif effect == "disco":
            hold = int(6000.0 / float(setting))
        elif setting <> "":
            hold = int(setting)

        if effect not in ["rainbow", "disco"]:
            entries += [
                {
                    "path" : str(i),
                    "name" : "%s %s" % (setting, unit),
                    "icon" : "icon_%s" % effect,
                    "node" : _build_menu_color("--" + effect, parameter = [ str(hold) ], normalize = effect == "pulse")
                }
            ]
        else:
            entries += [
                {
                    "path" : str(i),
                    "name" : "%s %s" % (setting, unit),
                    "icon" : "icon_%s" % effect,
                    "send" : ["--" + effect, hold],
                    "msg" : "Start %s with %s %s" % (effect, setting, unit)
                }
            ]

    return entries




def _build_active_timer_entries(status):

    entries = []
    activeTimer = _active_timer(status)

    if activeTimer:

        info = ""
        a = 0
        for i in range(4):
            name, exact = _get_light_name(status["timer"][i]["color"][5:-1].split(","))
            name = ("kind of " if not exact else "") + name
            start = status["timer"][i]["start"]
            runtime = status["timer"][i]["runtime"]
            if start <> "n/a":
                info += "\n" if a == 2 else ", " if a > 0 else ""
                info += "%s +%smin. turn %s" % (start, runtime, name)
                a = a + 1

        entries += [
            {
                "path" : "info",
                "name" : info,
                "icon" : "icon_program",
                "send" : ["--timer", "off"],
                "msg" : "Halt program"
            },
            {
                "path" : "program_off",
                "name" : "Halt program",
                "icon" : "icon_halt",
                "send" : ["--timer", "off"],
                "msg" : "Halt program"
            }
        ]

    return entries




def _build_menu_programs(status):

    entries = _build_active_timer_entries(status)

    for program in ["bgr", "wakeup", "doze", "ambient"]:
        if settings.getSetting("program_%s_enabled" % program) == "true":
            entries += [
                {
                    "path" : program,
                    "name" : program,
                    "icon" : "icon_%s" % program,
                    "node" : _build_menu_programs_duration(program)
                }
            ]

    return entries




def _build_menu_programs_duration(program):

    entries = []
    for i in range(5):

        setting = settings.getSetting("program_%s_min_%i" % (program, i))

        if program == "bgr":
            entries += [
                {
                    "path" : str(i),
                    "name" : "%s min." % setting,
                    "icon" : "icon_%s" % program,
                    "node" : _build_menu_programs_brightness(setting)
                }
            ]
        else:
            entries += [
                {
                    "path" : str(i),
                    "name" : "%s min." % setting,
                    "icon" : "icon_%s" % program,
                    "send" : ["--" + program, setting, 0],
                    "msg" : "Run program %s for %s min." % (program, setting)
                }
            ]

    return entries




def _build_menu_programs_brightness(duration):

    entries = []
    for i in range(4):
        setting = settings.getSetting("program_bgr_brightness_%i" % i)
        percent = round(100 * float(settings.getSetting("program_bgr_brightness_%i" % i)) / 255.0)
        entries += [
            {
                "path" : str(i),
                "name" : "%s (%i%%)" % (setting, percent),
                "icon" : "icon_bgr",
                "send" : ["--wheel", "bgr", duration, "0", setting],
                "msg" : "Run program bgr for %s min." % duration
            }
        ]

    return entries




def _build_dir_structure(path, url_params):

    global _menu

    splitted_path = path.split("/")
    splitted_path.pop(0)

    entries = []

    # root
    if path == "/":
        assigned_groups = 0
        for i in range(SLOTS):

            mac = settings.getSetting("dev_%i_mac" % i)
            alias = settings.getSetting("dev_%i_name" % i)
            enabled = settings.getSetting("dev_%i_enabled" % i)
            icon = BULB_ICONS[int(settings.getSetting("dev_%i_icon" % i))]
            groups = int(settings.getSetting("dev_%i_groups" % i))

            if mac == "" or enabled != "true":
                continue

            assigned_groups |= groups

            entries += [
                {
                    "path" : mac,
                    "name" : alias,
                    "icon" : icon,
                    "node" : []
                }
            ]

        for i in range(0, 5):
            if pow(2, i) & assigned_groups == pow(2, i):
                entries += [
                    {
                        "path" : "group_%i" % i,
                        "name" : settings.getSetting("group_%i" % i),
                        "icon" : "icon_group",
                        "node" : []
                    }
                ]

        if settings.getSetting("group_all") == "true":
            entries += [
                {
                    "path" : "group_all",
                    "name" : "All",
                    "icon" : "icon_group_all",
                    "node" : []
                }
            ]

    # device main menu with status
    elif path != "/" and len(splitted_path) > 0:
        status = None
        if "status" in url_params:
            status = json.loads(url_params["status"][0])

        target = splitted_path[0]
        entries = [
            {
                "path" : target,
                "node" : _build_menu(target, status)
            }
        ]

    _menu = [
        {
        "path" : "",
        "node" : entries
        }
    ]




def browse(path, url_params):

    try:
        _build_dir_structure(path, url_params)

        directory = _get_directory_by_path(path)
        for entry in directory["node"]:
            _add_list_item(entry, path)

        xbmcplugin.endOfDirectory(addon_handle)

    except BulbException:
        xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % ("Synchronization failed!",
                           "Try again!", addon_dir))




def _exec_mipows(threads):

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    time.sleep(0.4)




def execute(path, params):

    splitted_path = path.split("/")
    if len(splitted_path) < 2:
        return


    target = splitted_path[1]

    if "silent" not in params:
        xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % (params["msg"][0], "Sending data to bulb...", addon_dir))

    try:
        xbmc.log(" ".join(params["send"]), xbmc.LOGNOTICE);

        _max_parallel = int(settings.getSetting("threads"))
        threads = []

        for mac in _get_macs_of_target(target):

            threads.append(threading.Thread(target=_exec_mipow, args=(mac, params["send"])))
            
            if len(threads) > _max_parallel:
                _exec_mipows(threads)
                threads = []

        _exec_mipows(threads)
        

        if "silent" not in params:
            xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % (params["msg"][0], "successful", addon_dir))

            xbmc.executebuiltin('Container.Update("plugin://%s/%s","update")'
                        % (__PLUGIN_ID__, target))

    except BulbException:
        if "silent" not in params:
            xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % (params["msg"][0], "Failed! Try again", addon_dir))




if __name__ == '__main__':

    if sys.argv[1] == "discover":
        discover()
    else:
        addon_handle = int(sys.argv[1])
        path = urlparse.urlparse(sys.argv[0]).path
        url_params = urlparse.parse_qs(sys.argv[2][1:])

        if "send" in url_params:
            execute(path, url_params)
        else:
            browse(path, url_params)
