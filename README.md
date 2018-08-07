# kodi-addon-playbulb
KODI addon in order to control Mipow playbulb

This add-on allows you to control Mipow Playbulbs directly in Kodi. 

From a technical point of view this addon is based on the CLI project for playbulbs. Therefore usage is restricted to Linux and preconditions of the CLI project must also be fulfilled for this kodi addon. You might also visit [Mipow Playbulb BTL201](https://github.com/Heckie75/Mipow-Playbulb-BTL201) in order to get details how it works technically. 

# 1. Pre-conditions

As mentioned this addon has technical preconditions. `expect` must be installed if not done yet:

Install `expect`:
```
$ sudo apt install expect
```

In addition `gatttool`, which is a tool in order to talk to bluetooth LE devices, must be installed. Open a terminal windows and check if `gatttool` is available:
```
$ gatttool
Usage:
  gatttool [OPTION...]
...

```

# 2. Install addon

In order to install the addon the easiest way is to download the zip file [plugin.audio.playbulb.zip](/plugin.audio.playbulb.zip), navigate to *Addons > Addon-browser* and select *install from zip*. Perhaps, you must restart Kodi and activate the addon explicitly before it will be visible in *Addons > Music-Addons* list.

**Note:** Please remember that you can't install it on Windows, Mac and other platforms than Linux. 

# 3. Setup bulbs

Before you can control any bulbs the addon must know which bulbs are yours. In order to make them known, please go to addon's configuration and *start discovery*:

<img src="plugin.audio.playbulb/resources/assets/screenshot_14.png?raw=true">

Afterwards there should be a list of all Mipow playbulbs found in range.

Now you can start and playing around with your bulbs: 

List of bulbs:
<img src="plugin.audio.playbulb/resources/assets/screenshot_1.png?raw=true">

Bulb's main menu with current status:
<img src="plugin.audio.playbulb/resources/assets/screenshot_3.png?raw=true">

Built-in effects:
<img src="plugin.audio.playbulb/resources/assets/screenshot_9.png?raw=true">

Light programs:
<img src="plugin.audio.playbulb/resources/assets/screenshot_12.png?raw=true">

# 4. Configuring menues

You can change some configurations, i.e.:

Color presets:
<img src="plugin.audio.playbulb/resources/assets/screenshot_15.png?raw=true">

Effects speed:
<img src="plugin.audio.playbulb/resources/assets/screenshot_16.png?raw=true">

Program duration and a little bit more:
<img src="plugin.audio.playbulb/resources/assets/screenshot_17.png?raw=true">

I hope that you will enjoy it!