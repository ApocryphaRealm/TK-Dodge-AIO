# Changelog - TK Dodge AIO

TK Dodge AIO keeps its own version line from 1.0.0. It is a fork of TK Dodge RE Addon 3.1.5-era source by Styyx
(upstream numbering is not continued).

## 1.0.0 - 2026-09-15 - untested

### Added
- TK Dodge RE and TK Dodge RE Addon features in one SKSE plugin (`TK_Dodge_RE.dll`, replacing either of theirs) for
  Skyrim SE 1.5.97 on CommonLibSSE-NG: four-way dodge, step or roll, dodge in place, sprint-tap and sneak-tap dodge,
  double tap, input buffering, stamina cost (flat or percent, Actor Value Generator and Perk Entry Point Extender
  modifiers), perk lock, on-dodge spell, attack cancel with light-only and MCO recovery-window options, i-frame duration.
- Settings in `TK Dodge AIO.ini` and on an Apocrypha Menu Framework page.
- Main-loop hook mapped to SE (35565 + 0x731); vtable hooks on SprintHandler, SneakHandler and PlayerCharacter::Update.
