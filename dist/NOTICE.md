# TK Dodge AIO - copyright and licence

TK Dodge AIO is licensed under the **GNU General Public License, version 3 or (at your option) any later version**
(`LICENSE`). Copyright (C) 2026 ApocryphaRealm for the SE port and the Apocrypha Menu Framework settings page.

## What it is built from

| Part | Author | Licence | Source |
|---|---|---|---|
| TK Dodge RE Addon (this repository's upstream - dodge logic, input buffering, double tap, perk lock, on-dodge spell, stamina cost options, attack-cancel tuning) | Styyx | GPL-3.0 | https://github.com/Styyx1/TKDodgeAddon |
| TK Dodge RE (script-free TK Dodge the Addon grew from) | Maxsu, FBplus, Loop, Xing | MIT | https://github.com/max-su-2019/TK-Dodge-RE |
| TK Dodge SE (animations and the original design) | tktk | see its Nexus page | https://www.nexusmods.com/skyrimspecialedition/mods/15309 |
| StyyxUtils helpers (form-string lookup, mod-loaded check, menu check, ApplySpell) - rewritten in `src/Compat.h` | Styyx (ApplySpell credited to KernalsEgg / colinswrath) | GPL-3.0 | https://github.com/Styyx1/StyyxUtils |
| Perk Entry Point Extender API header | NoahBoddie | see `src/API` | https://www.nexusmods.com/skyrimspecialedition/mods/91192 |

## Statement of changes from the upstream Addon

- Ported from xmake and an AE-only CommonLib fork to CMake + vcpkg **CommonLibSSE-NG**, so it runs on Skyrim SE 1.5.97.
- Hooks rewritten onto `write_vfunc` and the SKSE trampoline; the main-loop call site mapped to SE (id 35565 + 0x731 /
  AE id 36564 + 0xC26) and byte-checked before it is patched.
- Settings moved from REX::TOML to `TK Dodge AIO.ini` (same key names), read and written with plain file I/O.
- The settings page is drawn on the Apocrypha Menu Framework: on/off switches, translation keys, AMF reserved keys
  refused at key capture.
- Trace logging by default with a level header; one log line per hook with its address; null checks on every lookup.

See `THIRD_PARTY_NOTICES.md` for the bundled libraries and assets.
