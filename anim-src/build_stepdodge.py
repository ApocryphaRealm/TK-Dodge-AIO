# build_stepdodge.py - builds our own LEFT step-dodge for Skyrim SE from scratch, in Blender 5.2 + PyNifly.
#
# Everything here is procedural: the pose of every frame is computed from our own key curves (COM path, foot plants,
# lean, guard), solved with our own two-bone IK, and keyed onto an armature built from the vanilla SE skeleton.hkx.
# No existing dodge animation is read for motion - only the reference clip's length and annotation list are reused
# (see reference_report.md) so the existing TK Dodge behaviour patch and motion data still fit.
#
# Run (PowerShell or cmd):
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup
#       --python-exit-code 1 --python build_stepdodge.py -- <stage> [<stage> ...]
# Stages: build   - armature, keyed action, markers, StepDodgeLeft.blend + StepDodgeLeft.hkx (SE, 64-bit)
#         verify  - re-import the exported hkx onto a fresh armature and compare with the skeleton + annotations
#         render  - skin the vanilla-proportioned body (HIMBO meshes from the load order) and render the preview
#
# Coordinates are Skyrim's: +Y forward, +X the actor's right, +Z up, game units (1 unit ~ 1.43 cm). The clip is
# in place at NPC Root [Root]; travel comes from the behaviour's animationdatasinglefile motion data, so every
# world-space plant below is turned into root-local space by subtracting the motion-data root path R(t).
import bpy, sys, os, math, json, struct, addon_utils
from math import radians
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
SKEL_HKX = r"D:\Modlists\Njordlinger\mods\Pandora Behaviour Engine Plus\Pandora_Engine\Skyrim\Template\actors\character\character assets\skeleton.hkx"
REF_HKX = r"D:\Modlists\Njordlinger\mods\test TK Dodge AIO 1.1.0\Meshes\Actors\Character\animations\TKDodge\StepDodgeLeft.hkx"
BODY_DIR = r"D:\Modlists\Njordlinger\mods\Highly Improved Male Body Overhaul (HIMBO)\meshes\actors\character\character assets"
BODY_NIFS = ["malebody_1.nif", "malehands_1.nif", "malefeet_1.nif"]
FPS = 30
DURATION = 0.7                      # = animationdatasinglefile tkds$2 duration (TKDodgeLeft)
NF = round(DURATION * FPS) + 1      # 22 sampled frames, f = 0..21 (Blender frames 1..22)

# Motion data of TKDodgeLeft (animationdatasinglefile DefaultMale~1\tkds$2.txt): time, x, y, z.
MOTION = [(0.0, 0.0), (0.06667, -23.0), (0.1, -45.0), (0.26667, -114.9), (0.53333, -214.1),
          (0.63333, -244.3), (0.66667, -250.0), (0.7, -251.7)]
# Annotations of the current clip (names and times kept identical; they mirror the motion data).
ANNOTATIONS = [(0.0, "animmotion 0 0 0"), (0.0667, "animmotion -23.0 0 0"), (0.1, "animmotion -45.0 0 0"),
               (0.2667, "animmotion -114.9 0 0"), (0.5333, "animmotion -214.1 0 0"),
               (0.6333, "animmotion -244.3 0 0"), (0.6667, "animmotion -250.0 0 0"),
               (0.7, "animmotion -251.7 0 0")]

addon_utils.enable("io_scene_nifly", default_set=True)
from io_scene_nifly.hkx import anim_skyrim as AS
from io_scene_nifly.hkx import anim_fo4 as AF
log = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); log.append(s)

# ------------------------------------------------------------------------------------------------ skeleton
def parse_vanilla_skeleton(path):
    """The vanilla SE skeleton.hkx carries a ragdoll and two hkaSkeletons, and its 64-bit hkaSkeleton fields sit 8
    bytes later than PyNifly's reader expects (name +24, parents +32, bones +48, pose +64, floats +80, slots +96), so
    PyNifly returns 0 bones for it. Read the 99-bone skeleton ourselves with PyNifly's section/fixup helpers."""
    data = open(path, "rb").read()
    secs = AS._parse_hkx_sections(data); ds = secs['__data__']; d = ds['offset']
    fx = AS._parse_local_fixups(data, ds)
    for rel, cls in AS._parse_virtual_fixups(data, ds, secs['__classnames__']['offset']):
        if cls != 'hkaSkeleton':
            continue
        s = d + rel
        cnt = lambda off: struct.unpack_from('<I', data, s + off + 8)[0]
        bones, lock = [], []
        bc = fx.get(rel + 48)
        for i in range(cnt(48)):
            br = bc + 16 * i
            bones.append(AS._read_null_string(data, d + fx[br]) if br in fx else "")
            lock.append(bool(data[d + br + 8]))
        if len(bones) != 99:
            continue
        sk = AF.Skeleton(name=AS._read_null_string(data, d + fx[rel + 24]), bones=bones, lock_translation=lock)
        pi = fx[rel + 32]
        sk.parents = [struct.unpack_from('<h', data, d + pi + 2 * i)[0] for i in range(cnt(32))]
        pc = fx[rel + 64]
        for i in range(cnt(64)):
            f = struct.unpack_from('<12f', data, d + pc + 0x30 * i)
            sk.reference_pose.append(AF.BonePose(list(f[0:3]), list(f[4:8]), list(f[8:11])))
        fc = fx.get(rel + 80)
        sk.reference_floats = [struct.unpack_from('<f', data, d + fc + 4 * i)[0] for i in range(cnt(80))] if fc is not None else []
        sc = fx.get(rel + 96)
        sk.float_slots = [AS._read_null_string(data, d + fx[sc + 8 * i]) for i in range(cnt(96))] if sc is not None else []
        return sk
    raise RuntimeError("no 99-bone hkaSkeleton in " + path)

VSK = parse_vanilla_skeleton(SKEL_HKX)

def import_armature(name="StepDodge_Skeleton"):
    """Build the armature with PyNifly's own HKX skeleton importer (so it carries PYN_HKX_BONES / game / pointer
    size exactly as PyNifly's exporter wants), feeding it the skeleton we parsed."""
    orig = AS.load_skyrim_skeleton
    AS.load_skyrim_skeleton = lambda p: VSK
    try:
        r = bpy.ops.import_scene.pynifly_hkx(filepath=SKEL_HKX, rename_bones=False, rename_bones_niftools=False,
                                             blender_xf=False, rotate_bones_pretty=False)
    finally:
        AS.load_skyrim_skeleton = orig
    arma = bpy.context.object
    assert arma and arma.type == 'ARMATURE', r
    arma.name = name
    arma['PYN_SKELETON_FILE'] = SKEL_HKX
    return arma

# Rest global transforms (armature space) straight from the skeleton.
def rest_globals():
    G = []
    for i, p in enumerate(VSK.reference_pose):
        t, r = p.translation, p.rotation
        m = Matrix.Translation(Vector(t)) @ Quaternion((r[3], r[0], r[1], r[2])).to_matrix().to_4x4()
        par = VSK.parents[i]
        assert par < i
        G.append(G[par] @ m if par >= 0 else m)
    return G
G0 = rest_globals()
BN = VSK.bones; IDX = {n: i for i, n in enumerate(BN)}; PAR = VSK.parents
L0 = [(G0[PAR[i]].inverted() @ G0[i]) if PAR[i] >= 0 else G0[i].copy() for i in range(len(BN))]
B0 = [g.to_3x3() for g in G0]
def P0(name): return G0[IDX[name]].translation.copy()

# ------------------------------------------------------------------------------------------------ curves
def mono(keys, f):
    """Monotone cubic (Fritsch-Carlson) through (frame, value) keys: eased, never overshoots a key."""
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]
    if f <= xs[0]: return ys[0]
    if f >= xs[-1]: return ys[-1]
    n = len(xs)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    m[0] = 0.0; m[-1] = 0.0                    # ease in and out at the ends
    for i in range(n - 1):
        if d[i] == 0: m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / d[i], m[i + 1] / d[i]
            s = a * a + b * b
            if s > 9: t = 3 / math.sqrt(s); m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]
    for i in range(n - 1):
        if xs[i] <= f <= xs[i + 1]:
            h = xs[i + 1] - xs[i]; t = (f - xs[i]) / h
            h00 = 2*t**3 - 3*t**2 + 1; h10 = t**3 - 2*t**2 + t; h01 = -2*t**3 + 3*t**2; h11 = t**3 - t**2
            return h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]

def root_x(f):
    """Motion-data root travel (linear between keys, as the engine reads it)."""
    t = f / FPS
    for (t0, x0), (t1, x1) in zip(MOTION, MOTION[1:]):
        if t <= t1: return x0 + (x1 - x0) * (t - t0) / (t1 - t0)
    return MOTION[-1][1]

def Rax(axis, deg):
    return Matrix.Rotation(radians(deg), 3, axis)

# ------------------------------------------------------------------------------------------------ the motion
# All positions WORLD (floor) space; root-local = world - (root_x(f), 0, 0).
K = dict(
    # body (COM) lag behind the capsule (+ = to the actor's right of the root). It holds still while the capsule
    # starts (anticipation), is thrown left by the push, leads a little while braking, and settles on the root.
    com_off_x=[(0, 0), (1, 11), (2, 21), (3, 29), (4, 32), (6, 22), (9, 2), (13, -12), (17, -9), (21, 0)],
    com_y=[(0, 0.5), (4, -1), (12, 1.5), (21, 0.5)],
    # height: dip (load) -> push extension -> low hop apex -> landing compression -> back to the combat stance
    com_z=[(0, 64.5), (2, 60), (4, 61.5), (8, 64.5), (13, 58.5), (15, 56), (18, 61.5), (21, 64.5)],
    hip_roll=[(0, 0), (2, 2.5), (5, -5), (9, -7), (13, -3), (16, 2), (19, 0.5), (21, 0)],    # about +Y; - leans left
    hip_pitch=[(0, -2), (2, -5), (5, -3), (9, -2), (14, -5), (18, -3), (21, -2)],           # about +X; - leans forward
    hip_yaw=[(0, 0), (3, -2), (8, 4), (14, 2), (21, 0)],                                     # about +Z
    spine_roll=[(0, 0), (2, 2), (5, -5), (9, -7), (13, -3), (16, 2), (19, 0), (21, 0)],
    spine_pitch=[(0, -3), (2, -5), (13, -5), (21, -3)],
    # feet: anchor = where the flat foot's ankle sits over the floor; lift = height above it; heel = toe-down degrees
    # (pivot at the ball while > 0, at the heel while < 0)
    lf_x=[(0, -14), (2, -14), (3, -20), (8, -130), (13, -232), (15, -257), (17, -265.7), (21, -265.7)],
    lf_y=[(0, 4), (2, 4), (8, 2), (13, 3), (21, 4)],
    lf_lift=[(0, 0), (1, 0), (2, 0.5), (4, 5), (7, 9), (10, 7), (12, 2.5), (13, 0), (21, 0)],
    lf_heel=[(0, 0), (1, 5), (2, 14), (3, 10), (6, 0), (11, -3), (13, 0), (21, 0)],
    rf_x=[(0, 14), (4, 14), (5, 8), (10, -110), (15, -215), (17, -237.7), (21, -237.7)],
    rf_y=[(0, -5), (4, -5), (10, -2), (17, -5), (21, -5)],
    rf_lift=[(0, 0), (4, 0), (5, 2), (7, 9), (10, 10), (14, 6), (16, 2), (17, 0), (21, 0)],
    rf_heel=[(0, 0), (2, 4), (3, 15), (4, 28), (5, 30), (8, 5), (13, 0), (21, 0)],
    # guard: hand targets in the chest's frame (given in rest-pose coordinates), plus small balance offsets
    lh_dx=[(0, 0), (4, -4), (9, -6), (14, -2), (21, 0)], lh_dz=[(0, 0), (4, 2), (9, 3), (14, -1), (21, 0)],
    rh_dx=[(0, 0), (5, 2), (10, 3), (15, 0), (21, 0)], rh_dz=[(0, 0), (5, -1), (12, -2), (21, 0)],
)
LH_GUARD = Vector((-10.0, 14.0, 97.0)); RH_GUARD = Vector((10.0, 12.0, 95.0))
def k(name, f): return mono(K[name], f)

def ik2(s, t, l1, l2, pole):
    """Two-bone IK: joint position for root s, target t (clamped to reach), bending toward pole."""
    v = t - s; dist = v.length; d = v.normalized()
    dist_c = min(max(dist, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
    t = s + d * dist_c
    cos_a = (l1 * l1 + dist_c * dist_c - l2 * l2) / (2 * l1 * dist_c)
    a = math.acos(max(-1, min(1, cos_a)))
    p = (pole - d * pole.dot(d)).normalized()
    return s + (d * math.cos(a) + p * math.sin(a)) * l1, t, dist / (l1 + l2)

def frame_of(a, n):
    a = a.normalized(); n = (n - a * n.dot(a)).normalized(); c = a.cross(n)
    return Matrix((a, n, c)).transposed()

def chain_rot(a0, b0, a1, b1):
    """World rotation taking the rest chain plane (a0 = bone dir, b0 = next bone dir) onto the posed one."""
    n0 = a0.cross(b0); n1 = a1.cross(b1)
    if n0.length < 1e-4 or n1.length < 1e-4:
        return a0.rotation_difference(a1).to_matrix()
    return frame_of(a1, n1) @ frame_of(a0, n0).transposed()

FINGERS = {}
def finger_setup():
    for side in "LR":
        H = P0(f"NPC {side} Hand [{side}Hnd]")
        I = P0(f"NPC {side} Finger10 [{side}F10]"); Pk = P0(f"NPC {side} Finger40 [{side}F40]")
        n = (I - H).cross(Pk - H).normalized()
        if (n.x > 0) != (side == "L"):    # palm faces the thigh in the rest A-pose: +X for the left hand
            n = -n
        for fi in range(5):
            names = [f"NPC {side} Finger{fi}{j} [{side}F{fi}{j}]" for j in range(3)]
            pts = [P0(x) for x in names]
            dirs = [(pts[1] - pts[0]), (pts[2] - pts[1]), (pts[2] - pts[1])]
            curl = (18, 28, 20) if fi == 0 else (55, 80, 50)
            for j, nm in enumerate(names):
                dd = dirs[j].normalized(); ax = dd.cross(n).normalized()
                FINGERS[IDX[nm]] = Rax(ax, curl[j])
finger_setup()

def solve_pose(f):
    """World (root-local) 4x4 for every bone at frame f (0..NF-1)."""
    rx = root_x(f); RO = Vector((rx, 0, 0))
    G = [None] * len(BN)
    delta = {}                                   # bone -> extra rotation in rest-world axes
    over = {}                                    # bone -> forced global rotation (3x3)
    com = IDX["NPC COM [COM ]"]
    com_pos = Vector((k("com_off_x", f), k("com_y", f), k("com_z", f)))      # root-local already (offset from root)
    Rhip = Rax('Z', k("hip_yaw", f)) @ Rax('Y', k("hip_roll", f)) @ Rax('X', k("hip_pitch", f))
    sr, sp, sy = k("spine_roll", f) / 3, k("spine_pitch", f) / 3, -0.8 * k("hip_yaw", f) / 3
    for nm in ("NPC Spine [Spn0]", "NPC Spine1 [Spn1]", "NPC Spine2 [Spn2]"):
        delta[IDX[nm]] = Rax('Z', sy) @ Rax('Y', sr) @ Rax('X', sp)
    for i, R in FINGERS.items(): delta[i] = R
    feet = {}
    for side, pre in (("L", "lf"), ("R", "rf")):
        A = P0(f"NPC {side} Foot [{side}ft ]"); T = P0(f"NPC {side} Toe0 [{side}Toe]")
        fwd = Vector(((T - A).x, (T - A).y, 0)).normalized(); lat = fwd.cross(Vector((0, 0, 1)))
        heel_pt = A + Vector((0, 0, -A.z)) - fwd * 3.0           # back of the heel on the floor
        anchor = Vector((k(pre + "_x", f) - rx, k(pre + "_y", f), A.z))      # flat-foot ankle position, root-local
        lift = k(pre + "_lift", f); p = k(pre + "_heel", f)
        Rf = Rax(lat, -p)
        if p >= 0:   pivot = anchor + (T - A)                              # ball of the foot
        else:        pivot = anchor + (heel_pt - A)
        ankle = pivot + Rf @ (anchor - pivot) + Vector((0, 0, lift))
        feet[side] = (ankle, Rf, lift <= 0.05 and p >= 0)
    reach = {}
    for i in range(len(BN)):
        par = PAR[i]; name = BN[i]
        if i == com:
            G[i] = Matrix.Translation(com_pos) @ (Rhip @ B0[i]).to_4x4(); continue
        base = (G[par] @ L0[i]) if par >= 0 else L0[i].copy()
        if i in delta:
            base = base @ (B0[i].transposed() @ delta[i] @ B0[i]).to_4x4()
        G[i] = base
        # legs
        for side in "LR":
            th, ca, fo, to = (IDX[f"NPC {side} Thigh [{side}Thg]"], IDX[f"NPC {side} Calf [{side}Clf]"],
                              IDX[f"NPC {side} Foot [{side}ft ]"], IDX[f"NPC {side} Toe0 [{side}Toe]"])
            if i == th:
                ankle, Rf, grounded = feet[side]
                s = G[i].translation
                h0, k0, a0 = P0(BN[th]), P0(BN[ca]), P0(BN[fo])
                l1, l2 = (k0 - h0).length, (a0 - k0).length
                pole = Vector((0.25 if side == "R" else -0.25, 1, 0))
                knee, ank, r = ik2(s, ankle, l1, l2, pole); reach[side] = r
                Rt = chain_rot((k0 - h0).normalized(), (a0 - k0).normalized(), (knee - s).normalized(), (ank - knee).normalized())
                Rc = chain_rot((a0 - k0).normalized(), (k0 - h0).normalized() * -1, (ank - knee).normalized(), (knee - s).normalized() * -1)
                G[i] = Matrix.Translation(s) @ (Rt @ B0[th]).to_4x4()
                over[ca] = (knee, Rc); over[fo] = (ank, Rf); over[to] = (None, Rf if not grounded else Matrix.Identity(3))
        if i in over:
            pos, R = over[i]
            if pos is None: pos = G[i].translation
            G[i] = Matrix.Translation(pos) @ (R @ B0[i]).to_4x4()
        # arms: IK at the upper arm, hand targets carried by the chest
        for side in "LR":
            ua, fa, ha = IDX[f"NPC {side} UpperArm [{side}Uar]"], IDX[f"NPC {side} Forearm [{side}Lar]"], IDX[f"NPC {side} Hand [{side}Hnd]"]
            if i == ua:
                ch = IDX["NPC Spine2 [Spn2]"]
                pre = "lh" if side == "L" else "rh"
                tgt_rest = (LH_GUARD if side == "L" else RH_GUARD) + Vector((k(pre + "_dx", f), 0, k(pre + "_dz", f)))
                tgt = G[ch] @ (G0[ch].inverted() @ tgt_rest)
                s = G[i].translation
                s0, e0, w0 = P0(BN[ua]), P0(BN[fa]), P0(BN[ha])
                l1, l2 = (e0 - s0).length, (w0 - e0).length
                pole_rest = Vector((-1 if side == "L" else 1, -0.3, -1.2))
                pole = G[ch].to_3x3() @ B0[ch].transposed() @ pole_rest
                el, wr, r = ik2(s, tgt, l1, l2, pole); reach["arm" + side] = r
                Ru = chain_rot((e0 - s0).normalized(), (w0 - e0).normalized(), (el - s).normalized(), (wr - el).normalized())
                Rl = chain_rot((w0 - e0).normalized(), -(e0 - s0).normalized(), (wr - el).normalized(), -(el - s).normalized())
                G[i] = Matrix.Translation(s) @ (Ru @ B0[ua]).to_4x4()
                over[fa] = (el, Rl)
        # head level and facing forward: neck takes half of the chest's rotation back out, the head all of it
        if name == "NPC Neck [Neck]":
            acc = (G[par].to_3x3() @ B0[par].transposed()).to_quaternion()
            Rn = acc.slerp(Quaternion(), 0.5).to_matrix()
            G[i] = Matrix.Translation(G[i].translation) @ (Rn @ B0[i]).to_4x4()
        if name == "NPC Head [Head]":
            G[i] = Matrix.Translation(G[i].translation) @ B0[i].to_4x4()
    return G, reach, feet

# ------------------------------------------------------------------------------------------------ build stage
def clear_scene():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)

def build():
    clear_scene()
    sc = bpy.context.scene
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NF
    arma = import_armature()
    arma.data.display_type = 'STICK'
    # the root path from the motion data, on an empty the armature rides (preview only - not part of the clip)
    mr = bpy.data.objects.new("MotionData_Root (preview travel)", None); sc.collection.objects.link(mr)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'     # motion data is read linearly
    for t, x in MOTION:
        mr.location = (x, 0, 0); mr.keyframe_insert("location", frame=1 + t * FPS)
    arma.parent = mr
    action = bpy.data.actions.new("StepDodgeLeft")
    arma.animation_data_create(); arma.animation_data.action = action
    for b in arma.data.bones:
        try: b.select = False
        except Exception: pass
    Cfix = {}
    worst = 0
    for b in arma.data.bones:
        i = IDX[b.name]; Cfix[i] = G0[i].inverted() @ b.matrix_local
        worst = max(worst, max(abs(Cfix[i][r][c] - (1 if r == c else 0)) for r in range(4) for c in range(4)))
    say("bone-vs-skeleton rest frame max deviation:", round(worst, 5))
    prevq = {}
    reach_log = []
    for f in range(NF):
        G, reach, feet = solve_pose(f)
        reach_log.append({k_: round(v, 3) for k_, v in reach.items()})
        M = {i: G[i] @ Cfix[i] for i in Cfix}
        for pb in arma.pose.bones:
            i = IDX[pb.name]; b = pb.bone
            if b.parent:
                rest_rel = b.parent.matrix_local.inverted() @ b.matrix_local
                basis = rest_rel.inverted() @ (M[IDX[b.parent.name]].inverted() @ M[i])
            else:
                basis = b.matrix_local.inverted() @ M[i]
            loc, q, _ = basis.decompose()
            if pb.name in prevq and prevq[pb.name].dot(q) < 0: q = -q
            prevq[pb.name] = q
            pb.rotation_mode = 'QUATERNION'
            pb.location = loc; pb.rotation_quaternion = q
            pb.keyframe_insert("location", frame=f + 1); pb.keyframe_insert("rotation_quaternion", frame=f + 1)
    say("leg/arm reach (target distance / chain length, >1 means clamped):")
    for f, r in enumerate(reach_log): say("  f%02d" % f, r)
    action.use_frame_range = True; action.frame_start = 1; action.frame_end = NF
    for t, name in ANNOTATIONS:
        fr = 1 + round(t * FPS)
        action.pose_markers.new(name).frame = fr
        sc.timeline_markers.new(name, frame=fr)
    bpy.context.view_layer.objects.active = arma; arma.select_set(True)
    hkx = os.path.join(OUT, "StepDodgeLeft.hkx")
    # PyNifly writes originalSkeletonName "Root"; vanilla clips (and the reference) say "NPC Root [Root]"
    orig_w = AS.write_skyrim_animation
    def w(path, anim, ptr_size=4):
        anim.original_skeleton_name = VSK.name
        return orig_w(path, anim, ptr_size=ptr_size)
    AS.write_skyrim_animation = w
    try:
        r = bpy.ops.export_scene.pynifly_hkx(filepath=hkx, game='SKYRIM_SE', fps=FPS, reference_skel=SKEL_HKX)
    finally:
        AS.write_skyrim_animation = orig_w
    say("export:", r, os.path.getsize(hkx) if os.path.exists(hkx) else "MISSING")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "StepDodgeLeft.blend"))

# ------------------------------------------------------------------------------------------------ verify stage
def verify():
    out = {}
    ours = AS.load_skyrim_animation(os.path.join(OUT, "StepDodgeLeft.hkx"))
    ref = AS.load_skyrim_animation(REF_HKX)
    for nm, a in (("ours", ours), ("reference", ref)):
        out[nm] = dict(duration=round(a.duration, 4), frames=a.num_frames, fps=round(1 / a.frame_duration, 3),
                       tracks=a.num_tracks, blend_hint=a.blend_hint, skeleton_name=a.original_skeleton_name,
                       binding=len(a.track_to_bone_indices),
                       annotations=[(round(x.time, 4), x.text) for x in a.annotations])
    # re-import with PyNifly onto a fresh armature and check bones, duration, markers and pose
    clear_scene()
    bpy.context.scene.render.fps = FPS
    arma = import_armature("Verify_Skeleton")
    bpy.context.view_layer.objects.active = arma; arma.select_set(True)
    r = bpy.ops.import_scene.pynifly_hkx(filepath=os.path.join(OUT, "StepDodgeLeft.hkx"))
    act = arma.animation_data.action
    out["reimport"] = dict(result=str(r), action=act.name, frame_range=list(act.frame_range),
                           markers=sorted([(m.frame, m.name) for m in act.pose_markers]),
                           armature_bones=len(arma.data.bones),
                           bones_match_skeleton=sorted(b.name for b in arma.data.bones) == sorted(BN),
                           hkx_bone_list_matches_skeleton_order=arma.get('PYN_HKX_BONES', '').split(';') == BN)
    # compare re-imported pose with the solver at a few frames (world positions of key joints)
    errs = []
    for f in (0, 5, 10, 15, 21):
        bpy.context.scene.frame_set(f + 1)
        G, _, _ = solve_pose(f)
        for nm in ("NPC COM [COM ]", "NPC L Foot [Lft ]", "NPC R Foot [Rft ]", "NPC L Hand [LHnd]", "NPC R Hand [RHnd]", "NPC Head [Head]"):
            pb = arma.pose.bones[nm]
            errs.append(((arma.matrix_world @ pb.matrix).translation - G[IDX[nm]].translation).length)
    out["reimport"]["max_joint_error_units"] = round(max(errs), 4)
    names_in_tracks = len(ours.tracks) == len(BN)
    out["track_count_equals_skeleton"] = names_in_tracks
    # which tracks actually move in ours
    moving = []
    for i, t in enumerate(ours.tracks):
        dt = max(math.dist(t.translations[0], x) for x in t.translations)
        dr = max(1 - abs(sum(p * q for p, q in zip(t.rotations[0], x))) for x in t.rotations)
        if dt > 0.01 or dr > 1e-6: moving.append(BN[i])
    out["ours_animated_bones"] = moving
    out["ours_root_track_static"] = BN[0] not in moving
    json.dump(out, open(os.path.join(OUT, "_verify.json"), "w"), indent=1)
    say(json.dumps(out, indent=1))

# ------------------------------------------------------------------------------------------------ render stage
def render():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "StepDodgeLeft.blend"))
    sc = bpy.context.scene
    arma = bpy.data.objects["StepDodge_Skeleton"]; mr = arma.parent
    sc.frame_set(1)
    # body: import each HIMBO mesh, then hand its skin over to our armature
    arma.data.pose_position = 'REST'
    for nif in BODY_NIFS:
        before = set(bpy.data.objects)
        for o in bpy.context.selected_objects: o.select_set(False)
        bpy.context.view_layer.objects.active = None
        bpy.ops.import_scene.pynifly(filepath=os.path.join(BODY_DIR, nif), blender_xf=False, rename_bones=False,
                                     rename_bones_niftools=False, rotate_bones_pretty=False, import_animations=False,
                                     import_collisions=False, import_tris=False, import_shapekeys=False)
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            if o.type == 'MESH':
                mw = o.matrix_world.copy()          # bind placement; our armature sits at the origin on frame 1
                for m in o.modifiers:
                    if m.type == 'ARMATURE': m.object = arma
                o.parent = arma; o.parent_type = 'OBJECT'
                o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = mw
                say("body mesh", o.name, len(o.data.vertices), "verts, groups", len(o.vertex_groups))
        for o in new:
            if o.type == 'ARMATURE': bpy.data.objects.remove(o)
            elif o.type == 'EMPTY' and not o.children: bpy.data.objects.remove(o)
    arma.data.pose_position = 'POSE'
    # simple head: a sphere on the head bone (the body meshes carry no head)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=16)
    head = bpy.context.object; head.name = "PreviewHead"
    head.scale = (5.6, 6.4, 7.2)
    hb = arma.data.bones["NPC Head [Head]"]
    head.parent = arma; head.parent_type = 'BONE'; head.parent_bone = hb.name
    sc.frame_set(1)
    hw = arma.matrix_world @ arma.pose.bones[hb.name].matrix
    head.matrix_world = Matrix.Translation(hw.translation + Vector((0, 1.0, 3.6))) @ Matrix.Diagonal((6.0, 7.0, 8.2, 1))
    bpy.ops.object.shade_smooth()
    # nose so facing direction reads
    bpy.ops.mesh.primitive_cone_add(radius1=1.2, depth=3)
    nose = bpy.context.object; nose.name = "PreviewNose"
    nose.parent = arma; nose.parent_type = 'BONE'; nose.parent_bone = hb.name
    nose.matrix_world = Matrix.Translation(hw.translation + Vector((0, 8.2, 4.2))) @ Rax('X', -90).to_4x4()
    # look: Workbench solid grey, neutral grey world, floor with a grid so foot plants read
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.72, 0.70, 0.67)
    sh.show_shadows = True; sh.show_cavity = True; sh.cavity_type = 'WORLD'
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.42, 0.42, 0.42)
    try: sc.display.shadow_focus = 0.2
    except Exception: pass
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-120, 0, -0.05)); fl = bpy.context.object; fl.name = "Floor"
    fl.scale = (700, 300, 1)
    mat = bpy.data.materials.new("floor"); mat.diffuse_color = (0.50, 0.50, 0.50, 1); fl.data.materials.append(mat)
    # grid lines every 20 units across x (shows plants vs. slide)
    gm = bpy.data.materials.new("grid"); gm.diffuse_color = (0.33, 0.33, 0.33, 1)
    for gx in range(-320, 81, 20):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(gx, 0, 0.0)); c = bpy.context.object
        c.scale = (0.5, 120, 0.12); c.data.materials.append(gm)
    for gy in range(-40, 41, 20):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-120, gy, 0.0)); c = bpy.context.object
        c.scale = (420, 0.5, 0.12); c.data.materials.append(gm)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in ("Floor",) and not o.data.materials:
            pass
    sh.color_type = 'MATERIAL'
    bodymat = bpy.data.materials.new("body"); bodymat.diffuse_color = (0.74, 0.71, 0.67, 1)
    for o in bpy.data.objects:
        if o.type == 'MESH' and (o.parent == arma):
            o.data.materials.clear(); o.data.materials.append(bodymat)
    nm = bpy.data.materials.new("nose"); nm.diffuse_color = (0.55, 0.35, 0.30, 1); nose.data.materials.clear(); nose.data.materials.append(nm)
    sc.render.resolution_x = 960; sc.render.resolution_y = 540; sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    # cameras: front (static, sees the whole lateral travel), side (rides the root, from the actor's left)
    def cam(name, loc, rot, ortho, parent=None):
        cd = bpy.data.cameras.new(name); cd.type = 'ORTHO'; cd.ortho_scale = ortho
        co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co)
        co.location = loc; co.rotation_euler = rot
        if parent: co.parent = parent
        return co
    # wide front: static, the whole lateral travel; close front and close side ride the root (motion data)
    wide = cam("CamWide", (-125, 600, 150), (radians(80), 0, radians(180)), 330)
    front = cam("CamFront", (0, 600, 66), (radians(90), 0, radians(180)), 150, parent=mr)
    side = cam("CamSide", (-600, 0, 66), (radians(90), 0, radians(-90)), 150, parent=mr)
    RES = {"CamWide": (1440, 540), "CamFront": (720, 720), "CamSide": (720, 720)}
    frames_dir = os.path.join(OUT, "_frames"); os.makedirs(frames_dir, exist_ok=True)
    # contact metrics on the evaluated feet mesh: lowest point per frame, and drift of the planted foot
    dg = bpy.context.evaluated_depsgraph_get()
    feet_obj = [o for o in bpy.data.objects if o.type == 'MESH' and 'feet' in o.name.lower()]
    for f in range(1, NF + 1):
        sc.frame_set(f)
        if feet_obj:
            ev = feet_obj[0].evaluated_get(dg); me = ev.to_mesh()
            zs = [(ev.matrix_world @ v.co) for v in me.vertices]
            lz = min(zs, key=lambda p: p.z)
            say("frame %02d feet lowest z %.2f at x %.1f" % (f, lz.z, lz.x)); ev.to_mesh_clear()
        for c in (front, side, wide):
            sc.camera = c
            sc.render.resolution_x, sc.render.resolution_y = RES[c.name]
            sc.render.filepath = os.path.join(frames_dir, f"{c.name}_{f:03d}.png")
            bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "_preview_scene.blend"))

if __name__ == "__main__":
    stages = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["build", "verify", "render"]
    for st in stages:
        {"build": build, "verify": verify, "render": render}[st]()
    open(os.path.join(OUT, f"_log_{'_'.join(stages)}.txt"), "w").write("\n".join(log))
