![](https://brands.home-assistant.io/_/litterrobot/icon.png)

# Litter-Robot for Home Assistant

Home Assistant custom integration for Litter-Robot Connect self-cleaning litter boxes, Feeder-Robot, and Whisker pet profiles.

Forked from [natekspencer/hacs-litterrobot](https://github.com/natekspencer/hacs-litterrobot) with added support for **Litter-Robot 5 / LR5 Pro**, **Feeder-Robot**, and **pet sensors**.

## Supported Devices

### Litter-Robot 3 Connect
- Waste drawer level, sleep mode sensors
- Night light switch, panel lockout switch
- Vacuum entity with clean cycle control

### Litter-Robot 5 / LR5 Pro
All LR3 entities plus:
- **Sensors**: Litter level, cycle count, pet weight, WiFi signal, sound volume, firmware, and 15+ diagnostic sensors
- **Binary sensors**: Drawer removed, bonnet removed, laser dirty, online status, smart weight (+ camera audio for Pro)
- **Controls**: Night light mode (Off/On/Auto), panel brightness, wait time, night light brightness/color
- **Switches**: Panel lockout, sleep mode (weekday/weekend with time pickers)
- **Buttons**: Clean cycle, reset waste drawer, recalibrate, change filter

### Feeder-Robot
- **Sensors**: Food level, food dispensed today, last feeding, next feeding
- **Controls**: Meal insert size, night light, panel lockout, gravity mode
- **Button**: Give snack
- **Binary sensor**: Online status

### Pet Profiles
- **Weight sensor** with full profile attributes (breed, age, birthday, diet, gender, health info)
- **Visits today** sensor (daily litter box visit count)

## Known Behavior

**Control refresh delay**: When you change a setting (e.g., wait time from 15 to 25 minutes), the UI may briefly show the new value, then revert to the old value while the robot processes the command. After approximately **9 seconds**, the integration re-polls the robot and the final confirmed state will appear. This is expected behavior — the integration sends the command immediately but waits ~8 seconds before refreshing to allow the robot's cloud API to reflect the change.

## Requirements

- `pylitterbot >= 2025.1.0b0` (with LR5 support)

## Installation

There are two main ways to install this custom component within your Home Assistant instance:

1. Using HACS (see https://hacs.xyz/ for installation instructions if you do not already have it installed):

   1. From within Home Assistant, click on the link to **HACS**
   2. Click on **Integrations**
   3. Click on the vertical ellipsis in the top right and select **Custom repositories**
   4. Enter the URL for this repository in the section that says _Add custom repository URL_ and select **Integration** in the _Category_ dropdown list
   5. Click the **ADD** button
   6. Close the _Custom repositories_ window
   7. You should now be able to see the _Litter-Robot_ card on the HACS Integrations page. Click on **INSTALL** and proceed with the installation instructions.
   8. Restart your Home Assistant instance and then proceed to the _Configuration_ section below.

2. Manual Installation:
   1. Download or clone this repository
   2. Copy the contents of the folder **custom_components/litterrobot** into the same file structure on your Home Assistant instance
      - An easy way to do this is using the [Samba add-on](https://www.home-assistant.io/getting-started/configuration/#editing-configuration-via-sambawindows-networking), but feel free to do so however you want
   3. Restart your Home Assistant instance and then proceed to the _Configuration_ section below.

While the manual installation above seems like less steps, it's important to note that you will not be able to see updates to this custom component unless you are subscribed to the watch list. You will then have to repeat each step in the process. By using HACS, you'll be able to see that an update is available and easily update the custom component.

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **Litter-Robot** and follow the setup flow
3. Enter your Whisker account credentials (same as the Whisker app)

---

## Support the Original Author

This integration is built on the work of [@natekspencer](https://github.com/natekspencer).

If you don't already own a Litter-Robot, please consider using [his referral code](https://www.pntrs.com/t/SENKTkpLSk1DSEtJTklPQ0hKS05HTQ) and get $25 off your own robot (as well as a tip to him in appreciation)!

If you already own a Litter-Robot and/or want to donate to him directly, consider buying him a coffee (or beer) instead by using the link below:

<a href="https://www.buymeacoffee.com/natekspencer" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-blue.png" alt="Buy Me A Coffee" height="41" width="174"></a>

## Credits

- Original integration and [pylitterbot](https://github.com/natekspencer/pylitterbot) library by [@natekspencer](https://github.com/natekspencer)
- LR5/LR5 Pro, Feeder-Robot, and pet profile support by [@blittenb](https://github.com/blittenb)
