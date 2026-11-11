# TK Dodge step dodges - reference facts and how our four clips match

These are our own replacements for the four TK Dodge step dodges: Left, Right, Forward and Back. They were authored
from scratch in Blender by `build_stepdodge.py`. From the current third-party clips we read only these things:
- length
- annotation list
- how root motion is carried
- which tracks are animated

None of their motion was copied, retargeted or traced. Every pose comes from our own key curves and IK solver.
`make_previews.py` turns the rendered frames into the preview videos and the contact sheet.

## Sources read
- Current clips: `D:\Modlists\Njordlinger\mods\test TK Dodge AIO 1.1.0\Meshes\Actors\Character\animations\TKDodge\StepDodge{Left,Right,Forward,Back}.hkx`.
  All four are Skyrim SE files (hk_2010, 64-bit), read with PyNifly's `anim_skyrim.load_skyrim_animation`.
- Behaviour patch, in `Nemesis_Engine\mod\tkds\`:
  - `1hm_behavior\` clip generators and their trigger arrays;
  - `animationdatasinglefile\DefaultMale~1\tkds$0..3.txt` motion data (DefaultFemale~1 is identical).
- Skeleton: the vanilla SE `skeleton.hkx` (99 bones). The copy used is Pandora's vanilla template at
  `mods\Pandora Behaviour Engine Plus\Pandora_Engine\Skyrim\Template\actors\character\character assets\skeleton.hkx`.
  No mod overrides the character skeleton.hkx, and every current clip has 99 tracks, which matches this skeleton.

## Facts shared by all four current clips
- 99 tracks, 1:1 with the skeleton (no explicit binding), blend hint NORMAL, originalSkeletonName "NPC Root [Root]".
- **In place.** NPC Root [Root] is identity for the whole clip, and so are the x_NPC Look/Translate/Rotate nodes.
  The travel comes from the motion data.
- In every clip NPC COM [COM ] translates (body bob and sway). In Right, NPC L/R Pauldron also translate.
- Annotations are `animmotion x y z` lines that repeat the motion-data keys. There are no `animrotation` lines.
- The behaviour's triggers live in the trigger arrays, not in the hkx: TKDodgeStop is relative to the clip end,
  TKDodgeRotation fires at 0.1 s, and there are events 21 and 22.

## Per direction
| | Left | Right | Forward | Back |
|---|---|---|---|---|
| Clip generator | `#tkds$16` TKDodgeLeft | `#tkds$5` TKDodgeRight | `#tkds$34` TKDodgeForward | `#tkds$25` TKDodgeBack |
| playbackSpeed | 1.0 | 1.0 | **0.9** | 1.0 |
| Triggers | Stop -0.002 from end; Rotation 0.1; 21 at 0.3; 22 at 0.5 | Stop -0.033 from end; Rotation 0.1; 21 at 0.1667; 22 at 0.5 | Stop -0.3 from end; Rotation 0.1; 21 at 0.3; 22 at 0.523 | Stop -0.08 from end; Rotation 0.1; 21 at 0.3333; 22 at 0.5 |
| Current hkx length | 0.6667 s, 20 frames (about 28.5 fps) | 0.6667 s, 21 frames (30 fps) | 0.8667 s, 26 frames (about 28.8 fps) | 0.6667 s, 20 frames (about 28.5 fps) |
| Current animated bones | 23 (COM, pelvis, legs, toes, spine, clavicles, arms, hands, neck, head) | 44 (the same plus skirt bones, pauldrons, twist bones, MagicEffectsNode) | 21 | 22 |
| Motion data | `tkds$2` | `tkds$3` | `tkds$0` | `tkds$1` |
| Motion duration | **0.7 s** | **0.7 s** | **0.866667 s** | **0.8 s** |
| Travel | **251.7 units along -X** (left, about 3.6 m) | **251.2 units along +X** (right) | **409.3 units along +Y** (forward, about 5.9 m) | **300.0 units along -Y** (back, about 4.3 m) |
| Motion keys (t: value) | .0667: -23.0; .1: -45.0; .2667: -114.9; .5333: -214.1; .6333: -244.3; .6667: -250.0; .7: -251.7 | .0667: 28.6; .1: 50.0; .2333: 102.0; .5333: 224.5; .6667: 251.2; .7: 251.2 | .0667: 12.963; .1333: 38.1847; .2333: 90.7585; .3667: 178.629; .5333: 291.939; .6333: 348.552; .7: 376.935; .7667: 395.209; .8667: 409.283 (x below 4e-5) | .1: -38.0; .1667: -78.5; .2667: -129.6; .4667: -223.2; .5333: -250.8; .5667: -265.2; .6: -278.6; .7: -296.5; .8: -300.0 |
| Annotations (all `animmotion`) | 8: `0 0 0` at 0, then one per motion key, `-23.0 0 0` ... `-251.7 0 0` | 7: `0 0 0` at 0, then one per motion key, `28.6 0 0` ... `251.2 0 0` (twice, at 0.6667 and 0.7) | 10: `0 0 0` at 0, then one per motion key, `0 12.963 0` ... `0 409.283 0` | 10: `0 0 0` at 0, then one per motion key, `0 -38.0 0` ... `0 -300.0 0` |
| **Ours: duration / frames** | 0.7 s / 22 at 30 fps | 0.7 s / 22 at 30 fps | 0.8667 s / 27 at 30 fps | 0.8 s / 25 at 30 fps |
| **Ours: annotations** | match, same names and times | match | match | match |

The current Back clip is 0.6667 s long, but its motion data and annotations run to 0.8 s. Ours is 0.8 s, so it
follows the motion data. The same goes for Left: 0.6667 s in the current file, 0.7 s in ours.

## Verification
After `verify`, each of our hkx files was re-imported with PyNifly onto a fresh armature. Results are in
`_verify_<Dir>.json`. All four passed:
- 99 tracks, with bone names and order the same as the vanilla skeleton.
- Duration equals the motion-data duration.
- The 8, 7, 10 and 10 annotation names are identical to the current clips, with times within 0.002 s.
- NPC Root [Root] is static; the clip is in place.
- Re-imported joint positions are within 0.04 units of the solver.

Our animated bones (18) are COM (translation and rotation), L/R Thigh, Calf, Foot and Toe0, Spine, Spine1, Spine2,
Neck, Head, and L/R UpperArm and Forearm. Pelvis, clavicles and hands follow their parents. Fingers hold a constant
loose-fist curl. Twist, skirt, pauldron, weapon and other helper bones stay at the skeleton's rest pose.

## How the motion matches the motion data
- Each clip is in place at the root. The body moves relative to a capsule that follows the motion-data path R(t).
- Foot plants were authored in world space and converted to root-local space by subtracting R(t), so planted feet stay put once the engine applies the motion data.
- The behaviour and motion data stay as they are.
- All four clips start and end in the same combat stance, so they blend alike:
  - COM at root-local (0, 0.5, 64.5);
  - left ankle at (-14, +4), right ankle at (+14, -5);
  - hips pitched -2 degrees, spine -3;
  - the same guard.

### Left (approved trial)
1. Anticipation dip with weight onto the right leg.
2. Push off the ball of the right foot.
3. Low lateral hop, leaning into the step.
4. The left foot lands on a straight braking leg, then skids about 34 units.
5. The right foot catches up and plants.
6. Compress, then settle.

### Right
The Left design mirrored across X in world space: feet, body path, hip and spine roll and yaw, guard offsets. Lateral
distances are scaled to 251.2/251.7 and laid onto Right's own motion data, so the plants stay planted with that path.
It was not hand-keyed. Two deliberate deviations from a strict mirror:
- the fore-aft (y) stance offsets stay with each foot's own side, so Right starts and ends in the same stance as the others;
- the guard's base hand positions are not swapped (only the offsets are mirrored).

### Forward
409 units in 0.87 s is far more than a single step can cover, so this is a lunge into a short run-out:
1. Anticipation dip with the body held back behind the capsule.
2. Push off the rear (right) foot.
3. A long, low lunge onto the left (f7).
4. Two quick running steps (right f12, left f17) with the trunk pitched forward up to about 19 degrees (hips plus spine).
5. Right then left catch-up steps into the stance (f22, f24).

There is a short flight between each step. Hip yaw counter-rotates with the steps, and the chest and head are kept
facing forward.

### Back
A hop-step backward:
1. Dip and lean forward over the front foot.
2. Push off the ball of the left foot.
3. Low hop back onto the right foot (f9).
4. The left foot catches up (f15).
5. The right steps back once more to brake (f19).
6. The left adjusts into the stance (f23).

## Limits
- PyNifly 28.3.0 reads 0 bones from the vanilla SE skeleton.hkx. That file has a ragdoll, and its 64-bit hkaSkeleton
  fields sit 8 bytes later than PyNifly expects. The build script parses the skeleton itself.
- The bundled hkxcmd is 32-bit and cannot open SE files, so PyNifly's reader is the only check on the files.
  None of the four has been loaded in the game.
- The Forward clip plays at 0.9 speed in the behaviour, so it takes about 0.96 s in game. Its motion data and
  duration match ours as authored.
- Preview body: HIMBO malebody_1, hands_1 and feet_1, skinned to our armature, with a sphere and a nose cone on the
  head bone in place of a head.
