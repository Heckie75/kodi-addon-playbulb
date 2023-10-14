import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.api.wrapper import mipow, requestSatus
from resources.lib.util import MAX_BULBS, createListItem, getLightName
from datetime import datetime, timedelta


class Playbulb():

    def __init__(self) -> None:

        self.addon = xbmcaddon.Addon()
        self._counterReset()

    def _counterReset(self, total=0):

        self._count = 0
        self._total = total

    def _getProgressHandler(self, heading: str, message: str, total):

        progress = xbmcgui.DialogProgressBG()
        progress.create(heading=heading, message=message)

        self._counterReset(total)

        def callback(message: str):
            self._count += 1
            xbmc.log(f"{self._count}\t{message.strip()}", xbmc.LOGINFO)
            if "ERROR" in message:
                raise Exception(message)
            progress.update(message=message.split("\t")[-1],
                            percent=int(100 * self._count / self._total))

        return progress, callback

    def selectBulb(self) -> 'list[xbmcgui.ListItem]':

        def _createListItemsForBulbs() -> 'list[xbmcgui.ListItem]':

            li = list()
            for i in range(MAX_BULBS):
                if not self.addon.getSettingBool(f"bulb_{i}_enable"):
                    continue

                label = self.addon.getSetting(f"bulb_{i}_name")
                label2 = self.addon.getSetting(f"bulb_{i}_mac")
                icon = self.addon.getSetting(f"bulb_{i}_icon")
                li.append(createListItem(label=label, label2=label2, icon=icon, rank=self.addon.getSettingInt(
                    f"bulb_{i}_order"), preselect=self.addon.getSettingBool(f"bulb_{i}_preselect")))

            li.sort(key=lambda i: (int(i.getProperty("rank")), i.getLabel()))
            return li

        def _rememberSelection(bulbs: 'list[xbmcgui.ListItem]') -> None:

            macs = [b.getLabel2() for b in bulbs]
            for i in range(MAX_BULBS):
                mac = self.addon.getSetting(f"bulb_{i}_mac")
                self.addon.setSettingBool(
                    f"bulb_{i}_preselect", mac in macs)

        options = _createListItemsForBulbs()
        preselection = [i for i in range(
            len(options)) if options[i].getProperty("preselect") == str(True)]
        selection = xbmcgui.Dialog().multiselect(heading=self.addon.getLocalizedString(
            32006), options=options, useDetails=True, preselect=preselection)
        if selection:
            bulbs = [options[i] for i in selection]
            _rememberSelection(bulbs=bulbs)
            return bulbs
        else:
            return None

    def colorMenu(self, pure: bool = False) -> 'tuple[int,int,int,int]':

        def _hex(f: float) -> str:

            return f"0{hex(int(min(255, max(0, f)))).replace('0x', '')}"[-2:]

        def _transform(s: str) -> 'tuple[int,int,int,int]':

            color = int(s, 16)
            red = color >> 16 & 0xff
            green = color >> 8 & 0xff
            blue = color & 0xff
            if red == green == blue:
                return (str(red), "0", "0", "0")
            else:
                return ("0", str(red), str(green), str(blue))

        colorlist: 'list[xbmcgui.ListItem]' = list()
        if pure:
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32125), label2="ffff0000"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32127), label2="ffffff00"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32123), label2="ff00ff00"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32124), label2="ff00ffff"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32122), label2="ff0000ff"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32126), label2="ffff00ff"))
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32128), label2="ffffffff"))
        else:
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32128 if i > 0 else 32121)} ({int(i*5100/255)}%)", label2=f"ff{_hex(i * 51) * 3}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32130)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 51)}{_hex(1 + i * 10)}00") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32125)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 51)}0000") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32127)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 51) * 2}00") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32131)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 10)}{_hex(1 + i * 51)}00") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32123)} ({int(i*5100/255)}%)", label2=f"ff00{_hex(1 + i * 51)}00") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32132)} ({int(i*5100/255)}%)", label2=f"ff00{_hex(1 + i * 51)}{_hex(1 + i * 10)}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32124)} ({int(i*5100/255)}%)", label2=f"ff00{_hex(1 + i * 51) * 2}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32122)} ({int(i*5100/255)}%)", label2=f"ff0000{_hex(1 + i * 51)}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32133)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 10)}00{_hex(1 + i * 51)}") for i in range(5, -1, -1)])
            colorlist.extend([xbmcgui.ListItem(
                label=f"{self.addon.getLocalizedString(32126)} ({int(i*5100/255)}%)", label2=f"ff{_hex(1 + i * 51)}00{_hex(1 + i * 51)}") for i in range(5, -1, -1)])
            colorlist.append(xbmcgui.ListItem(
                label=self.addon.getLocalizedString(32066), label2="00ffffff"))

        selectedcolor = None

        hexstr = xbmcgui.Dialog().colorpicker(
            heading=self.addon.getLocalizedString(32067), colorlist=colorlist, selectedcolor=selectedcolor)

        if not hexstr:
            return None

        elif hexstr == "00ffffff":
            ip = xbmcgui.Dialog().input(heading=self.addon.getLocalizedString(32066),
                                        type=xbmcgui.INPUT_IPADDRESS)
            return tuple(ip.split("."))
        else:
            return _transform(hexstr)

    def effectMenu(self) -> 'tuple[tuple,int]':

        def _handleRainbow() -> 'tuple[tuple,int]':
            while True:
                runtime = xbmcgui.Dialog().numeric(
                    heading=self.addon.getLocalizedString(32068), type=0, defaultt="255")
                if runtime is not None and 0 <= int(runtime) <= 255:
                    return ("--rainbow", runtime), 6

        def _handleCandle() -> 'tuple[tuple,int]':
            cmd = ["--candle"]
            color = self.colorMenu()
            if color:
                cmd.extend(color)
                return cmd, 6
            else:
                return None, None

        def _handleDisco() -> 'tuple[tuple,int]':
            while True:
                hold = xbmcgui.Dialog().numeric(
                    heading=self.addon.getLocalizedString(32069), type=0, defaultt="255")
                if hold is not None and 0 <= int(hold) <= 255:
                    return ("--disco", hold), 6

        def _handleBlink() -> 'tuple[tuple,int]':
            cmd = ["--flash"]
            color = self.colorMenu()
            if not color:
                return None, None
            cmd.extend(color)

            while True:
                hold = xbmcgui.Dialog().numeric(
                    heading=self.addon.getLocalizedString(32070), type=0, defaultt="10")
                if hold not in ("", None) and 0 <= int(hold) <= 255:
                    cmd.append(hold)
                    break

            while True:
                repetitions = xbmcgui.Dialog().numeric(
                    heading=self.addon.getLocalizedString(32071), type=0, defaultt="10")
                if repetitions not in (None, "") and 0 <= int(repetitions) <= 255:
                    cmd.append(repetitions)
                    break

            while True:
                pause = xbmcgui.Dialog().numeric(
                    heading=self.addon.getLocalizedString(32072), type=0, defaultt="10")
                if pause not in (None, "") and 0 <= int(pause) <= 255:
                    cmd.append(pause)
                    break

            return cmd, 6

        def _handlePulse() -> 'tuple[tuple,int]':
            cmd = ["--pulse"]
            color = self.colorMenu(pure=True)
            if not color:
                return None, None
            cmd.extend([str(min(1, int(c))) for c in color])

            while True:
                hold = xbmcgui.Dialog().numeric(
                    heading=self.addon.getLocalizedString(32073), type=0, defaultt="255")
                if hold not in (None, "") and 0 <= int(hold) <= 255:
                    cmd.append(hold)
                    return cmd, 6

        while True:
            heading = self.addon.getLocalizedString(32064)
            lis: 'list[xbmcgui.ListItem]' = list()
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32134), label2=self.addon.getLocalizedString(32140), icon="rainbow", command=["RAINBOW"]))
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32135), label2=self.addon.getLocalizedString(32141), icon="candle", command=["CANDLE"]))
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32136), label2=self.addon.getLocalizedString(32142), icon="disco", command=["DISCO"]))
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32137), label2=self.addon.getLocalizedString(32143), icon="blink", command=["BLINK"]))
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32138), label2=self.addon.getLocalizedString(32144), icon="pulse", command=["PULSE"]))
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32139), label2=self.addon.getLocalizedString(32145), icon="halt", command=["HALT"]))
            selection = xbmcgui.Dialog().select(heading=heading, list=lis, useDetails=True)

            if selection == -1:
                return None, None

            command = lis[selection].getProperty("command")
            if command == "RAINBOW":
                commands, steps = _handleRainbow()

            elif command == "CANDLE":
                commands, steps = _handleCandle()

            elif command == "DISCO":
                commands, steps = _handleDisco()

            elif command == "BLINK":
                commands, steps = _handleBlink()

            elif command == "PULSE":
                commands, steps = _handlePulse()

            elif command == "HALT":
                commands, steps = (("--halt"), 8)

            if commands:
                return commands, steps

    def securityMenu(self) -> 'tuple[tuple,int]':

        cmd = [f"--security"]
        start = xbmcgui.Dialog().input(
            heading=self.addon.getLocalizedString(32086), type=xbmcgui.INPUT_TIME)
        if start in ("", None):
            return None, None
        cmd.append(start.strip())

        end = xbmcgui.Dialog().input(
            heading=self.addon.getLocalizedString(32094), type=xbmcgui.INPUT_TIME)
        if end in ("", None):
            return None, None
        cmd.append(end.strip())

        while True:
            mintime = xbmcgui.Dialog().numeric(
                heading=self.addon.getLocalizedString(32095), type=0, defaultt="5")
            if mintime not in (None, "") and 0 < int(mintime) <= 255:
                cmd.append(mintime)
                break

        while True:
            maxtime = xbmcgui.Dialog().numeric(
                heading=self.addon.getLocalizedString(32096), type=0, defaultt="30")
            if maxtime not in (None, "") and 0 < int(maxtime) <= 255:
                cmd.append(maxtime)
                break

        color = self.colorMenu()
        if not color:
            return None, None
        cmd.extend(color)

        return tuple(cmd), 6

    def sceneMenu(self) -> 'tuple[tuple,int]':

        def _inOneMinute() -> str:

            then = datetime.now() + timedelta(minutes=1)
            return then.strftime("%H:%M")

        def _handleScene(scene: str) -> 'tuple[tuple,int]':
            cmd = [f"--{scene}"]
            runtime = xbmcgui.Dialog().input(
                heading=self.addon.getLocalizedString(32085), type=xbmcgui.INPUT_TIME, defaultt="01:00")
            if runtime in ("", None):
                return None, None
            cmd.append(runtime.strip())

            start = xbmcgui.Dialog().input(
                heading=self.addon.getLocalizedString(32086), type=xbmcgui.INPUT_TIME, defaultt=_inOneMinute())
            if start in ("", None):
                return None, None
            cmd.append(start.strip())

            return tuple(cmd), 12

        def _handleWheel() -> 'tuple[tuple,int]':

            cmd = [f"--wheel"]

            lis: 'list[xbmcgui.ListItem]' = list()
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32088), label2="", icon="bgr", preselect=True))
            lis.append(createListItem(
                label=self.addon.getLocalizedString(32089), label2="", icon="bgr"))
            lis.append(createListItem(
                label=self.addon.getLocalizedString(32090), label2="", icon="bgr"))
            selection = xbmcgui.Dialog().select(
                heading=self.addon.getLocalizedString(32087), list=lis, useDetails=True)
            if selection == -1:
                return None, None
            cmd.append(["bgr", "grb", "rbg"][selection])

            while True:
                brightness = xbmcgui.Dialog().numeric(
                    heading=self.addon.getLocalizedString(32091), type=0, defaultt="32")
                if brightness not in (None, "") and 0 < int(brightness) <= 255:
                    break

            _c, steps = _handleScene("wheel")
            if _c == None:
                return None, None
            cmd.extend(_c[1:])
            cmd.append(brightness)

            return tuple(cmd), steps

        while True:
            heading = self.addon.getLocalizedString(32075)
            lis: 'list[xbmcgui.ListItem]' = list()
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32078), label2=self.addon.getLocalizedString(32079), icon="wakeup", command=["WAKEUP"]))
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32076), label2=self.addon.getLocalizedString(32077), icon="ambient", command=["AMBIENT"]))
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32080), label2=self.addon.getLocalizedString(32081), icon="doze", command=["DOZE"]))
            lis.append(createListItem(label=self.addon.getLocalizedString(
                32082), label2=self.addon.getLocalizedString(32083), icon="bgr", command=["WHEEL"]))

            selection = xbmcgui.Dialog().select(heading=heading, list=lis, useDetails=True)

            if selection == -1:
                return None, None

            command = lis[selection].getProperty("command")
            if command == "WAKEUP":
                commands, steps = _handleScene("wakeup")

            elif command == "AMBIENT":
                commands, steps = _handleScene("ambient")

            elif command == "DOZE":
                commands, steps = _handleScene("doze")

            elif command == "WHEEL":
                commands, steps = _handleWheel()

            if commands:
                return commands, steps

    def deviceMenu(self, bulbs: 'list[xbmcgui.ListItem]', status: dict = None) -> 'xbmcgui.ListItem':

        def _buildSecurity(status: dict) -> xbmcgui.ListItem:

            if status["security"]["startingHour"] != 255:
                label = self.addon.getLocalizedString(32051)
                label2 = self.addon.getLocalizedString(32052) % (
                    status["security"]["start_str"], status["security"]["end_str"])
                icon = "random"
                return createListItem(label=label, label2=label2, icon=icon,
                                      notification=label, command=["--security", "off", "--off"], steps=6)
            else:
                label = self.addon.getLocalizedString(32093)
                icon = "random"
                return createListItem(label=label, label2="", icon=icon,
                                      notification=label, command=["SET_SECURITY"])

        def _buildTurnLightOff(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32053)
            name, file, exact = getLightName(status["color"])
            label2 = self.addon.getLocalizedString(
                32054) + (self.addon.getLocalizedString(32055) if not exact else "") + name
            icon = "bulb_%s" % file
            return createListItem(label=label, label2=label2,
                                  icon=icon, notification=label, command=["--off"], steps=6)

        def _buildTurnLightOn(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32056)
            name, file, exact = getLightName(status["color"])
            label2 = self.addon.getLocalizedString(
                32054) + (self.addon.getLocalizedString(32055) if not exact else "") + name
            icon = "bulb_on"
            return createListItem(label=label, label2=label2,
                                  icon=icon, notification=label, command=["--on"], steps=6)

        def _buildToggleLight(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32057)
            name, file, exact = getLightName(status["effect"]["color"])
            label2 = self.addon.getLocalizedString(
                32054) + (self.addon.getLocalizedString(32055) if not exact else "") + name
            icon = "bulb_%s" % file
            return createListItem(label=label, label2=label2,
                                  icon=icon, notification=label, command=["--toggle"], steps=10)

        def _buildLightUp(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32058)
            name, file, exact = getLightName(status["color"])
            label2 = self.addon.getLocalizedString(
                32054) + (self.addon.getLocalizedString(32055) if not exact else "") + name
            icon = "bulb_up"
            return createListItem(label=label, label2=label2,
                                  icon=icon, notification=label, command=["--up"], steps=8)

        def _buildLightDown(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32059)
            name, file, exact = getLightName(status["color"])
            label2 = self.addon.getLocalizedString(
                32054) + (self.addon.getLocalizedString(32055) if not exact else "") + name
            icon = "bulb_down"
            return createListItem(label=label, label2=label2,
                                  icon=icon, notification=label, command=["--down"], steps=8)

        def _buildSetLight(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32060)
            name, file, exact = getLightName(status["color"])
            label2 = self.addon.getLocalizedString(
                32054) + (self.addon.getLocalizedString(32055) if not exact else "") + name
            icon = "presets"
            return createListItem(label=label, label2=None,
                                  icon=icon, notification=label, command=["SET_COLOR"])

        def _buildTurneffectOff(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32061)
            name, file, exact = getLightName(status["effect"]["color"])
            label2 = self.addon.getLocalizedString(
                32062) % status['effect']['type_str']
            label2 += (self.addon.getLocalizedString(32055)
                       if not exact else "") + name
            icon = status["effect"]["type_str"]
            return createListItem(label=label, label2=label2,
                                  icon=icon, notification=label, command=["--off"], steps=6)

        def _buildTurneffectHalt(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32063)
            name, file, exact = getLightName(status["effect"]["color"])
            label2 = self.addon.getLocalizedString(
                32062) % status['effect']['type_str']
            label2 += (self.addon.getLocalizedString(32055)
                       if not exact else "") + name
            icon = "halt"
            return createListItem(label=label, label2=label2,
                                  icon=icon, notification=label, command=["--halt"], steps=8)

        def _buildRunEffect(status: dict) -> xbmcgui.ListItem:
            label = self.addon.getLocalizedString(32064)
            icon = "effect"
            return createListItem(label=label, label2=None,
                                  icon=icon, notification=label, command=["SET_EFFECT"])

        def _buildActiveScene(status: dict) -> 'list[xbmcgui.ListItem]':

            lis: 'list[xbmcgui.ListItem]' = list()
            labels2: 'list[str]' = list()
            for t in status["timers"]["timers"]:
                if t["time_str"] == "--:--":
                    continue

                name, file, exact = getLightName(t["color"])
                labels2.append(
                    "%s +%s %s %s" % (t["time_str"], t["runtime_str"], self.addon.getLocalizedString(32084), name))

            if labels2:
                lis.append(createListItem(label="Stop scene", label2=" | ".join(
                    labels2), icon="halt", command=["--timer", "off", "--off"], steps=12))

            return lis

        def _buildScene(status: dict) -> 'list[xbmcgui.ListItem]':

            lis = _buildActiveScene(status=status)
            label = self.addon.getLocalizedString(32074 if lis else 32075)
            icon = "program"
            lis.append(createListItem(label=label, label2="",
                       icon=icon, notification=label, command=["SET_SCENE"]))
            return lis

        if not status or len(status) == 0:
            return

        lis: 'list[xbmcgui.ListItem]' = list()

        heading = " | ".join([b.getLabel() for b in bulbs])

        if status[0]["effect"]["type"] != 255:
            lis.append(_buildTurnLightOn(status[0]))
            lis.append(_buildTurnLightOff(status[0]))
            lis.append(_buildTurneffectOff(status[0]))
            lis.append(_buildTurneffectHalt(status[0]))

        elif status[0]["color"]["color_str"] != "off":
            lis.append(_buildTurnLightOff(status[0]))
            lis.append(_buildToggleLight(status[0]))
            lis.append(_buildSetLight(status[0]))
            # lis.append(_buildLightUp(status[0]))
            # lis.append(_buildLightDown(status[0]))

        elif status[0]["color"]["color_str"] == "off":
            lis.append(_buildTurnLightOn(status[0]))
            lis.append(_buildSetLight(status[0]))
            lis.append(_buildToggleLight(status[0]))

        lis.extend(_buildScene(status[0]))
        lis.append(_buildRunEffect(status[0]))
        lis.append(_buildSecurity(status[0]))

        selection = xbmcgui.Dialog().select(heading=heading, list=lis, useDetails=True)
        if selection == -1:
            return None
        else:
            return lis[selection]

    def play(self) -> None:

        def _requestStatus(lis: 'list[xbmcgui.ListItem]') -> dict:

            retry = True
            while retry:
                progress, callback = self._getProgressHandler(heading=self.addon.getLocalizedString(32001),
                                                              message=self.addon.getLocalizedString(32003), total=2 + 15 * len(lis))
                try:
                    return requestSatus(macs=[li.getLabel2()
                                              for li in lis], callback=callback)
                except Exception as ex:
                    xbmc.log(str(ex), xbmc.LOGERROR)
                    retry = xbmcgui.Dialog().yesno(heading=self.addon.getLocalizedString(
                        32001), message=self.addon.getLocalizedString(32092), autoclose=30000)
                finally:
                    progress.close()

        bulbs = self.selectBulb()
        if not bulbs:
            return

        status = _requestStatus(bulbs)
        if status == None:
            return

        args = [s["address"] for s in status]
        args.extend(["--log", "INFO"])
        steps = 0

        while True:
            li = self.deviceMenu(bulbs, status=status)
            if not li:
                return

            command = li.getProperty("command")
            if command == "SET_COLOR":
                color = self.colorMenu()
                if color:
                    steps = 6
                    args.append("--color")
                    args.extend(color)
                    break

            elif command == "SET_EFFECT":
                command, steps = self.effectMenu()
                if command:
                    args.extend(command)
                    break

            elif command == "SET_SCENE":
                command, steps = self.sceneMenu()
                if command:
                    args.extend(command)
                    break

            elif command == "SET_SECURITY":
                command, steps = self.securityMenu()
                if command:
                    args.extend(command)
                    break

            else:
                steps = int(li.getProperty("steps"))
                args.extend(command.split("|"))
                break

        retry = True
        while retry and args:
            progress, callback = self._getProgressHandler(heading=" | ".join(
                s["name"] for s in status), message=self.addon.getLocalizedString(32065), total=2 + len(bulbs) * steps)
            try:
                mipow(args, callback=callback)
                retry = False
            except:
                retry = xbmcgui.Dialog().yesno(heading=self.addon.getLocalizedString(
                    32001), message=self.addon.getLocalizedString(32092), autoclose=30000)
            finally:
                progress.close()
