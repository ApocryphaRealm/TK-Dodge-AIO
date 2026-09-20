TK Dodge AIO
Version 1.0.2

WHAT IT IS
TK Dodge RE and TK Dodge RE Addon in one SKSE plugin for Skyrim SE 1.5.97, with its settings on an Apocrypha Menu Framework page and in TK Dodge AIO.ini. Four-way dodge, step or roll, dodge in place, sprint-tap and sneak-tap dodge, double tap, input buffering, stamina cost (flat or percent, with Actor Value Generator and Perk Entry Point Extender modifiers), perk lock, on-dodge spell, attack cancel with light-only and MCO recovery-window options, i-frame duration. The package carries the animations and the behaviour patch the dodge needs, so nothing else from the TK Dodge family is installed beside it.

WHAT CHANGED
Version 1.0.2
Fixed the T-pose when dodging with magic in hand: the package carried behaviour files generated years ago (meshesctors\characterehaviors and _1stpersonehaviors, plus an old animationdatasinglefile.txt) that outranked the behaviour engine's own output wherever the mod sat above it in the load order, and the magic graph in them had none of the current clips. Those files are gone; Pandora's output is the only behaviour now. Run Pandora once after updating.

Version 1.0.1
Fixed dodging on the way out of a menu: a tap whose press began while a menu held input is never a dodge, however slowly the menu closes, and a release the plugin never saw the press for is refused outright. Covers the Sprint and Sneak tap dodges as well as the dodge key, and the quest journal as well as the System tab.
Added the Address Library check before anything else: a missing file for this game version is named in the log and on screen and the plugin loads inert.
Added the eleven translation files for the settings page.

Version 1.0.0
First SE build of the combined dodge plugin, with every Addon option on an Apocrypha Menu Framework page and in TK Dodge AIO.ini.

INSTALL
Disable TK Dodge RE, TK Dodge For RE, TK Dodge RE Addon, TK Dodge Animation Pandora Patch and TK First Person Fix for Pandora; this package carries their files.
Run Pandora with "TK Dodge AIO" ticked (the behaviour patch keeps its code tkds and the TKDodge animation names, so other TK Dodge patches still line up).
Optional: Apocrypha Menu Framework for the settings page; without it the INI is read at start.

SETTINGS
Journal > System > Mod Configuration > TK Dodge AIO (Apocrypha Menu Framework), or edit TK Dodge AIO.ini. Changes on the page apply at once; Save keeps them.

LOG
Documents\My Games\Skyrim Special Edition\SKSE\TK Dodge AIO.log, at trace by default (uLogLevel=0). One line per hook with its address at start, and the reason whenever a dodge is refused.

LICENCE AND CREDIT
GPL-3.0-or-later (LICENSE-TKDodgeAIO-GPL-3.0.txt). Built from Styyx's TK Dodge RE Addon (GPL-3.0) and Maxsu's TK Dodge RE (MIT); animations by tktk (TK Dodge SE); the Pandora patch by Xingda666 with tktk's permission; the first-person fix by ThorKirienko. NOTICE.md and THIRD_PARTY_NOTICES.md carry every notice and say exactly what came from where.
