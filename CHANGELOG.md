# Changelog - TK Dodge AIO

TK Dodge AIO keeps its own version line from 1.0.0. It is a fork of TK Dodge RE Addon 3.1.5-era source by Styyx
(upstream numbering is not continued).

## 1.0.1 - 2026-09-16 - untested

### Fixed
- **The menu-exit guard now covers the SPRINT and SNEAK tap dodges, which is how the dodge is actually triggered** (the owner, 2026-09-16: *"TK dodges guard against dodging out of the quest journal menu did not work"*). The guard added above sits in the dodge-KEY sink, and with `bUseSprintKey` on - the owner's setup, where a tap of Sprint dodges - the dodge comes from `SprintHandlerHook::ProcessButton` instead, which the guard never touched. Both hook paths tested `IsInMenu` but not the moment just after a menu closed, which is exactly where the press that left the menu lands. They now check the same grace, so leaving the journal no longer dodges whichever key is doing the dodging.
- **No dodge on the press that closes a menu** (the owner, 2026-09-16: *"we need to add to tk dodge that you dont dodge when exiting out of a menu - it currently dodges when exiting the journal but not the system tab"*). The dodge sink already ignored a press made WHILE a menu is open, but that check cannot catch the press that closes one: the game hands it to gameplay in the same breath as the close, by which point the menu is no longer open and the press reads as an ordinary dodge. Whether it slipped through came down to how many frames the close took - which is exactly why leaving the journal dodged and leaving from its System tab, a frame slower, did not. A `MenuOpenCloseEvent` sink now remembers when one of the watched menus closed, and a dodge press within `fMenuExitGrace` seconds of that (default 0.25, 0 turns the guard off) is ignored. Only the menus a dodge is already blocked inside are watched, so closing something unrelated cannot eat a dodge, and the span is measured on the steady clock because the game clock stops in menus.

## 1.0.0 - 2026-09-15 - untested

### Added
- TK Dodge RE and TK Dodge RE Addon features in one SKSE plugin (`TK_Dodge_RE.dll`, replacing either of theirs) for
  Skyrim SE 1.5.97 on CommonLibSSE-NG: four-way dodge, step or roll, dodge in place, sprint-tap and sneak-tap dodge,
  double tap, input buffering, stamina cost (flat or percent, Actor Value Generator and Perk Entry Point Extender
  modifiers), perk lock, on-dodge spell, attack cancel with light-only and MCO recovery-window options, i-frame duration.
- Settings in `TK Dodge AIO.ini` and on an Apocrypha Menu Framework page.
- Main-loop hook mapped to SE (35565 + 0x731); vtable hooks on SprintHandler, SneakHandler and PlayerCharacter::Update.
