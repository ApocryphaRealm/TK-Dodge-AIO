# StepDodgeLeft - reference facts and how our clip matches

Trial 1 of our own TK Dodge replacement animations. This is the LEFT step dodge, authored from scratch in Blender
(build_stepdodge.py). Of the current third-party clip we read only its length, its annotation list, how it carries
root motion and which tracks it animates. None of its motion was copied, retargeted or traced. Every pose comes from
our own key curves and IK solver.

## Files read
- Current clip: `D:\Modlists\Njordlinger\mods\test TK Dodge AIO 1.1.0\Meshes\Actors\Character\animations\TKDodge\StepDodgeLeft.hkx`
  (Skyrim SE, hk_2010, 64-bit, 8352 bytes), read with PyNifly's `anim_skyrim.load_skyrim_animation`.
- Behaviour patch: `Nemesis_Engine\mod\tkds\1hm_behavior\#tkds$16.txt` (clip generator), `#tkds$15.txt` (its triggers),
  `animationdatasinglefile\DefaultMale~1\TKDodgeLeft~tkds$2.txt` and `tkds$2.txt` (motion data). DefaultFemale has the same data.
- Skeleton: the vanilla SE `skeleton.hkx` (99 bones, from Pandora's vanilla template:
  `mods\Pandora Behaviour Engine Plus\Pandora_Engine\Skyrim\Template\actors\character\character assets\skeleton.hkx`).
  No mod in the load order overrides the character skeleton.hkx, so the game uses the vanilla one. The current clip has
  99 tracks, which is that skeleton's bone count.

## Current clip (StepDodgeLeft.hkx)
| Item | Value |
|---|---|
| Duration (hkx header) | 0.6667 s |
| Frame count | 20 (frame duration 0.0351 s, about 28.5 fps; the clip was probably authored at 30 fps and saved as 20 frames over 0.6667 s) |
| Tracks | 99, no explicit track-to-bone binding (1:1 with the skeleton), blend hint NORMAL, originalSkeletonName "NPC Root [Root]" |
| Root motion | **In place.** NPC Root [Root] (track 0) is identity for the whole clip. So are x_NPC LookNode / Translate / Rotate. The only bone that translates is NPC COM [COM ] (body bob and sway, 15 units at most). The travel comes from the motion data. |
| Animated bones (23) | NPC COM, Pelvis, L/R Thigh, Calf, Foot, Toe0, Spine, Spine1, Spine2, L/R Clavicle, UpperArm, Forearm, Hand, Neck, Head. Fingers and the other bones are static. |
| Annotations (8) | 0.0000 `animmotion 0 0 0`; 0.0667 `animmotion -23.0 0 0`; 0.1000 `animmotion -45.0 0 0`; 0.2667 `animmotion -114.9 0 0`; 0.5333 `animmotion -214.1 0 0`; 0.6333 `animmotion -244.3 0 0`; 0.6667 `animmotion -250.0 0 0`; 0.7000 `animmotion -251.7 0 0` (the last one is past the clip's own 0.6667 s end) |

## Behaviour patch
- Clip generator `#tkds$16` "TKDodgeLeft": `animationName Animations\TKDodge\Stepdodgeleft.hkx`, MODE_SINGLE_PLAY,
  playbackSpeed 1, no crop, no enforced duration.
- Its triggers (`#tkds$15`) live in the behaviour, not in the hkx: TKDodgeStop at -0.002 s from the end of the clip;
  TKDodgeRotation at 0.1 s; event id 21 at 0.3 s; event id 22 at 0.5 s.
- Motion data `tkds$2`: **duration 0.7 s**. 7 translation keys, all along -X (the actor's left):
  0.06667 -23.0 | 0.1 -45.0 | 0.26667 -114.9 | 0.53333 -214.1 | 0.63333 -244.3 | 0.66667 -250.0 | 0.7 -251.7.
  One rotation key (0.7, identity). Total travel is 251.7 units (about 3.6 m).

## How our clip matches
| Item | Ours |
|---|---|
| Duration | **0.7 s**, the same as the motion data. 22 frames at exactly 30 fps. (The old hkx said 0.6667 s. The brief asked for the motion-data length, so the last motion key and the TKDodgeStop trigger now land at the clip's end.) |
| Skeleton / tracks | 99 tracks on the vanilla skeleton, same bone names and order (checked on re-import). Explicit 1:1 binding. originalSkeletonName "NPC Root [Root]". |
| Root motion | In place, like the reference: NPC Root [Root] is static. The body motion is relative to a capsule that moves along the motion-data path R(t). Foot plants were authored in world space and turned into root-local space by subtracting R(t), so planted feet stay put once the engine applies the motion data. The motion data and the behaviour are unchanged. |
| Annotations | The same 8 names at the same times. Re-import gives 0.0, 0.0667, 0.1, 0.2667, 0.5333, 0.6333, 0.6667 and 0.7 s with identical text. |
| Animated bones (18) | COM (translation and rotation), L/R Thigh, Calf, Foot, Toe0, Spine, Spine1, Spine2, Neck, Head, L/R UpperArm and Forearm. Pelvis, clavicles and hands follow their parents. Fingers hold a constant loose-fist curl. Twist, weapon and other helper bones stay at the skeleton's rest pose. |

## Motion (left step dodge, no roll)
Frames run f0 to f21 at 30 fps.
- **f0-f2:** combat stance, then an anticipation dip (COM drops about 4.5 units) while weight shifts onto the right leg. The left heel unweights. The capsule is already moving, so the body holds still for a moment.
- **f2-f4:** the right leg pushes off on the ball of the foot (heel rises 28 degrees) and the left foot lifts out low.
- **f4-f13:** low lateral hop. The COM rises about 3 units. The hips and spine lean into the travel direction (left), up to about 12 degrees combined.
- **f13:** the left foot lands with an almost straight braking leg, then skids about 34 units as it decelerates (f13-f17). Its lowest point stays at sole height throughout.
- **f17:** the right foot catches up and plants beside it. COM compresses (f15 is lowest), then rises and settles back into the start stance at f21 so the clip blends.
- **Throughout:** the head stays level and faces forward (neck takes half of the chest's rotation back out, the head all of it). Both hands stay in a guard in front of the chest, carried by the chest, with small balance offsets.

Every curve is a monotone cubic with eased ends (no linear motion and no overshoot), sampled once per frame.

## Notes and limits
- PyNifly 28.3.0 reads 0 bones from the vanilla SE skeleton.hkx. That file has a ragdoll, and its 64-bit hkaSkeleton
  fields sit 8 bytes later than PyNifly expects. The build script parses the skeleton itself and gives it to PyNifly's
  importer.
- The bundled hkxcmd is 32-bit and cannot open SE files, so validation is PyNifly's own reader, plus the round trip
  back onto a fresh armature (largest joint error 0.03 units). The file has not been loaded in the game.
- Preview body: HIMBO malebody_1, hands_1 and feet_1 from the load order, skinned to our armature, with a sphere and a
  nose cone on the head bone in place of a head.
