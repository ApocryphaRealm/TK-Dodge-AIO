# 8-way dodge behaviour patch - report (2026-11-11)

Patch folder: `D:\Claude output\6. current wip mods\TK-Dodge-AIO\dist\Nemesis_Engine\mod\tkds\`
New events: TKDodgeForwardLeft, TKDodgeForwardRight, TKDodgeBackLeft, TKDodgeBackRight.
The edits were made by a script, `patch8way.py`, and checked by a second script, `verify8way.py`. Both are in the session scratchpad. A copy of the folder as it was before the edit is in the scratchpad under `tkds_backup`. No git, Pandora or game was run.

All touched files are CRLF with tab indentation, like the originals. Nothing existing was changed except three `numelements` values and two state lists in our own nodes (listed below). Everything else is added lines.

## Files edited (16)

| File | What was added |
|---|---|
| `1hm_behavior\#0085.txt` | 4 event names, appended at the end of the eventNames MOD_CODE block (after Collision_Cancel) |
| `1hm_behavior\#0087.txt` | 4 eventInfos `{flags 0}`, at the end of the eventInfos MOD_CODE block |
| `1hm_behavior\#0088.txt` | 4 wildcard transitions, at the end of the existing MOD_CODE block |
| `1hm_behavior\#tkds$42.txt` | states list numelements 4 -> 8, plus `#tkds$73 #tkds$81 #tkds$89 #tkds$97` |
| `magicbehavior\#0077.txt` / `#0079.txt` | 4 event names after SoundPlay; 4 eventInfos |
| `magicbehavior\#tkds$8.txt` | This is the magic graph's wildcard transition array (our own node, set as wildcardTransitions of `#1346`). Transitions numelements 4 -> 8, plus 4 transitions |
| `magicbehavior\#tkds$43.txt` | states list numelements 4 -> 8, plus `#tkds$72 #tkds$80 #tkds$88 #tkds$96` |
| `_1stperson\1hm_behavior\#0085.txt` / `#0087.txt` | 4 event names; 4 eventInfos |
| `_1stperson\1hm_behavior\#0088.txt` | 4 wildcard transitions |
| `_1stperson\magicbehavior\#0077.txt` / `#0079.txt` | 4 event names; 4 eventInfos |
| `_1stperson\magicbehavior\#1016.txt` | 4 wildcard transitions |
| `defaultmale\#0029.txt`, `defaultfemale\#0029.txt` | `Animations\TKDodge\StepDodgeForwardLeft.hkx`, `...ForwardRight`, `...BackLeft`, `...BackRight` |

## New nodes - 1hm_behavior (`#tkds$66` to `#tkds$97`, 32 files)

The dodge state machine is `#tkds$42`. The parent state is 5695600. The modifier `#tkds$11` is shared.

| Diagonal | effect (cloned from) | step triggers (cloned from) | step clip | binding set | selector `[roll,roll,step,step]` | modifier gen | enterNotify | StateInfo / stateId |
|---|---|---|---|---|---|---|---|---|
| ForwardLeft | 66 (Forward `$3`) | 67 (Left `$15`) | 68 | 69 | 70 = `$36 $36 $68 $68` | 71 | 72 | 73 / 4 |
| ForwardRight | 74 (`$3`) | 75 (Right `$4`) | 76 | 77 | 78 = `$36 $36 $76 $76` | 79 | 80 | 81 / 5 |
| BackLeft | 82 (Back `$0`) | 83 (`$15`) | 84 | 85 | 86 = `$27 $27 $84 $84` | 87 | 88 | 89 / 6 |
| BackRight | 90 (`$0`) | 91 (`$4`) | 92 | 93 | 94 = `$27 $27 $92 $92` | 95 | 96 | 97 / 7 |

- The roll clips reused are Forward = `#tkds$36` (SneakRun_ForwardRoll) and Back = `#tkds$27` (DodgeBack).
- The new step clips are named after the event, e.g. `TKDodgeForwardLeft`, with `animationName` `Animations\TKDodge\StepDodge<Diag>.hkx`.
- Each enterNotifyEvents copy holds event id 460 (a hard number), the same as the existing four.
- Transitions in `#0088` use toStateId 5695600, toNestedStateId 4, 5, 6 or 7, condition null, and flags `FLAG_TO_NESTED_STATE_ID_IS_VALID|FLAG_IS_LOCAL_WILDCARD|FLAG_DISABLE_CONDITION` (copied from the Forward and Back transitions).

## New nodes - magicbehavior (`#tkds$65` to `#tkds$96`, 32 files)

The dodge state machine is `#tkds$43`. The parent state is 5695600. The modifier `#tkds$16` is shared.

In this graph each existing transition has its own `hkbExpressionCondition` (`(iRightHandType == 8) || (iRightHandType == 9)`). So each new transition also gets its own cloned condition. The existing magic StateInfos have enterNotifyEvents = null, so the new ones have no enterNotify copy either.

| Diagonal | condition (from) | effect (from) | step triggers (from) | step clip | binding set | selector | modifier gen | StateInfo / stateId |
|---|---|---|---|---|---|---|---|---|
| ForwardLeft | 65 (`$0`) | 66 (Forward `$1`) | 67 (Left `$9`) | 68 | 69 | 70 = `$38 $38 $68 $68` | 71 | 72 / 4 |
| ForwardRight | 73 (`$0`) | 74 (`$1`) | 75 (Right `$27`) | 76 | 77 | 78 = `$38 $38 $76 $76` | 79 | 80 / 5 |
| BackLeft | 81 (`$6`) | 82 (Back `$7`) | 83 (`$9`) | 84 | 85 | 86 = `$22 $22 $84 $84` | 87 | 88 / 6 |
| BackRight | 89 (`$6`) | 90 (`$7`) | 91 (`$27`) | 92 | 93 | 94 = `$22 $22 $92 $92` | 95 | 96 / 7 |

- The roll clips reused are Forward = `#tkds$38` and Back = `#tkds$22`.
- The flags are `FLAG_TO_NESTED_STATE_ID_IS_VALID|FLAG_IS_LOCAL_WILDCARD`, copied from the existing ones.
- The existing magic states are named State0 to State3. The new ones are named after the event, as briefed.

## First person - effect nodes REUSED, no new nodes

- **`_1stperson\1hm_behavior\#0088`**:
  - ForwardLeft and ForwardRight go to nested state 3 with effect `#tkds$3`. That is the same state and effect TKDodgeForward uses.
  - BackLeft and BackRight go to nested state 2 with effect `#tkds$0`, the same as TKDodgeBack.
  - Condition null, flags copied (including FLAG_DISABLE_CONDITION).
- **`_1stperson\magicbehavior\#1016`**:
  - The forward diagonals go to nested state 4, with effect `#0082` and condition `#1015`, the same as TKDodgeForward.
  - The back diagonals go to nested state 3, with effect `#tkds$35` and condition `#1015`, the same as TKDodgeBack.
  - Flags are `FLAG_TO_NESTED_STATE_ID_IS_VALID`.
- Precedent for sharing an effect: this graph already uses `#tkds$35` for three transitions.

## animationdatasinglefile - motion ids 4-7 (same in DefaultMale~1 and DefaultFemale~1)

The ids in use before this change were 0-3 in both folders. The male and female files are byte-identical, as the existing pairs are.

| Clip generator | clip entry file | motion file | duration | keys |
|---|---|---|---|---|
| TKDodgeForwardLeft | `TKDodgeForwardLeft~tkds$4.txt` | `tkds$4.txt` | 0.7 | 7 |
| TKDodgeForwardRight | `TKDodgeForwardRight~tkds$5.txt` | `tkds$5.txt` | 0.7 | 6 |
| TKDodgeBackLeft | `TKDodgeBackLeft~tkds$6.txt` | `tkds$6.txt` | 0.7 | 7 |
| TKDodgeBackRight | `TKDodgeBackRight~tkds$7.txt` | `tkds$7.txt` | 0.7 | 6 |

Clip entry shape: name, `tkds$M`, `1`, `0`, `0`, `0`.

Motion file shape: name, duration, key count, `time x y 0` lines, `1`, `0.7 0 0 0 1`, then a blank line. This copies `tkds$2.txt` and `tkds$3.txt` exactly.

The values come from `diag_motion.json`, with times to 5 decimals and values to 1 decimal, like `tkds$2` and `tkds$3`. For example, ForwardLeft is `0.06667 -20.7 20.7 0` ... `0.7 -226.3 226.3 0`. FirstPerson~1 was not touched.

## Verification results (all passed)

- **References:** every `#tkds$N` referenced exists in its folder, and no id is defined twice:

  | Folder | Nodes defined | Distinct ids referenced |
  |---|---|---|
  | 1hm | 98 | 98 |
  | magic | 97 | 97 |
  | 1st 1hm | 34 | 34 |
  | 1st magic | 36 | 36 |

- **File names:** each file's object name matches its file name.
- **Well-formed:** every touched file has as many `<hkobject` as `</hkobject>`, and no touched file has a bare LF.
- **numelements:** checked against the real list length in EVERY `#tkds$*` node file, the new ones and the old ones. There were no mismatches.
- **Event order:** the new names are the last 4 of each eventNames block. Vanilla names and infos are equal, and the mod-block names and infos are equal, in every graph:

  | Graph | Vanilla names = infos | Mod-block names = infos |
  |---|---|---|
  | 1hm | 461 | 14 |
  | magic | 97 | 15 |
  | 1st 1hm | 461 | 12 |
  | 1st magic | 97 | 13 |

  All eventInfos are `flags 0`, so their order cannot differ.
- **Additions only:** a line diff against the backup shows only inserts, apart from the three intended changes (`#tkds$42` and `#tkds$43` states, and `#tkds$8` numelements). No files were removed.

## Uncertain points and judgement calls

1. **No time-0 key in the motion files (judgement call).** `diag_motion.json` has a key at time 0 with value (0,0). I left it out, because none of the existing four motion files has a time-0 key; they all start at 0.06667. So the key counts are 7 and 6, the same as Left (7) and Right (6). If the engine wants the time-0 key, add it back and add 1 to the counts.
2. **Rounding to 1 decimal (judgement call).** I rounded to match the existing style. This loses up to 0.05 units per key.
3. **Which step clip was cloned (judgement call).** Each new step clip is a clone of the same-side cardinal step clip (Left or Right). That gives playbackSpeed 1.0. The Forward step clip has 0.9; the Left, Right and Back clips have 1.0. With 1.0, the 0.7 s clip runs at its authored length and matches the motion data.
4. **The reused roll clips carry the cardinal's name (guess about effect).** The Forward roll clip is named TKDodgeForward, so a diagonal roll uses TKDodgeForward's animationdata entry (`tkds$0`, the forward step motion), and the same goes for Back. That is already how the cardinal rolls work, because the step and roll clips of each direction share one name. I did not change it.
5. **enterNotifyEvents id 460 (copied as is).** It is a hard event index, not `$eventID[...]$`. In both 1hm graphs that index is the last vanilla event, not one of ours. I copied it as it stands; I did not check what it is meant to be.
6. **The new .hkx files are not checked here.** The patch expects `Animations\TKDodge\StepDodgeForwardLeft.hkx` (and the other three) to exist in the shipped animations folder, with the exact case used here. I did not check that.
7. **Not run through Pandora or Nemesis.** The patch has not been built yet, so it is proven only by the static checks above.
