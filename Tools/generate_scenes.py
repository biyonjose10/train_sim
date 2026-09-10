"""
Builds both playable scenes from his SampleScene.unity.

Scene 1 is his scene with the wiring it was missing: the train moved back so it has an approach,
a stop waypoint where he had parked it, the brake script attached, painted signal lamps, an
approach signal on a trigger, a follow camera, and the station.

Scene 2 is the same file with the train already stopped and the boarding sequence on top.

Both are generated from his scene rather than from the asset pack's demo scene, so the lighting,
skybox, rails, signal and directional light are his by construction. That is what stops the fog
and the broken purple sky coming back.

The station and the terrain are lifted as literal YAML blocks out of the pack's scene and
re-anchored, so their layout cannot drift from what the pack author placed.

Deterministic: same inputs, same fileIDs, so re-running never breaks a reference.
"""

import hashlib
import math
import os
import re

REPO = r"C:\Users\biyon\projects\train_sim"
SCENE1_SRC = os.path.join(REPO, "Assets", "Scenes", "SampleScene.unity")
SCENE1_OUT = SCENE1_SRC
SCENE2_OUT = os.path.join(REPO, "Assets", "Scenes", "Scene2_StationBoarding.unity")
PACK = os.path.join(REPO, "Assets", "pixel horror abandoned rural  train station",
                    "Scenes", "environment with station.unity")

# ---------------------------------------------------------------- identity

TRAIN_GUID = "7899c5f46e2286e4692bfa57b2f6c8e5"
TRAIN_GO, TRAIN_TR = 5680802176122678309, 8443818322557161937

# His rails, so the catenary that ships inside the rail prefab can be switched off
# where it stands in front of the signal.
RAIL_GUID = "5134ed3777d4c484d8fe19fd21f2cc1e"
RAIL_GO, RAIL_TR = 2171760524236046288, 1623647493005633391
RAIL_WIRE_GO = 6962243738968842197   # the "wire straight" child
RAIL_SEGMENT_LENGTH = 101.76         # a segment covers (pivot - length) .. pivot
# Mixamo "Louise" with an In Place walk clip. The asset pack figure it replaces was a bare
# mannequin with no animation at all.
PERSON_GUID = "c6785175debea5949a9e9556321b2d5f"      # Passengers/Louise@Walking.fbx
PERSON_GO, PERSON_TR = 919132149155446097, -8679921383154817045
PERSON_ANIMATOR = 5866666021909216657
PERSON_CONTROLLER = "d00cc9a58a621744f9de3897b4f90ad3"  # Passengers/Passenger.controller

MAT_RED = "a05474e98d8e14850be3e19a5f0a45b5"      # New Material.mat
MAT_YELLOW = "4edc65da92c7a4841b08cbd2e1ff65ea"   # New Material 3.mat
MAT_DARK = "9fa6d9495e43248479959c8c53531c6e"     # New Material 2.mat

MESH = "0000000000000000e000000000000000"
MESH_CUBE, MESH_CYLINDER, MESH_SPHERE = 10202, 10206, 10207


def guid_for(p):
    return hashlib.md5(("train_sim::" + p).encode()).hexdigest()


MAT_GREEN = guid_for("Assets/Materials/Signal Green.mat")
SCRIPTS = {n: guid_for("Assets/" + n + ".cs") for n in
           ("Scene2Director", "PassengerWalker", "TrainSpaceDrive",
            "TrainFollowCamera", "ArriveAtStationLoader")}
# His two scripts keep their own guids.
SCRIPTS["TrainStationButtonStop"] = None   # filled in from the meta at run time
SCRIPTS["Signal1Trigger"] = None

# ---------------------------------------------------------------- layout

TRAIN_X, TRAIN_Y = -2.4, 0.55
TRAIN_START_Z = -95.0          # short run-in, stays on the terrain
TRAIN_STOP_Z = -44.46          # exactly where he parked it: nose 2 units short of the signal
END_OF_TRACK_Z = 90.0
APPROACH_SIGNAL_Z = -70.0      # midway along the run-in

SIGNAL_SCALE = 1.3712
SIGNAL_POS_Z = 18.459      # his station signal, on the line
APPROACH_SIGNAL_POS = (-5.9773, 3.0711, APPROACH_SIGNAL_Z)

PLATFORM_X, PLATFORM_TOP_Y = -6.9, 2.04   # Mixamo root sits at the feet
DOOR_LINE_X = -3.0
DOOR_LOCAL_Z = [35.46, 41.46, 47.46, 53.46]

SHOTS = [
    ("Cam_Station_A", (-9.8, 3.9, -14.0), (-4.6, 2.4, 2.0), True),
    ("Cam_Station_B", (-5.6, 2.9, -6.5), (-3.8, 2.3, 3.0), False),
    ("Cam_Station_C", (7.4, 3.8, -8.0), (-5.6, 2.8, 15.0), False),
]
# Top middle third person, tight on the front of the train: on the centre line, 52 forward of
# the pivot, which is only 9 units behind the nose, and 2.4 above the carriage roof. Looking
# down the track keeps the signal in frame, and being closer makes it read larger when it
# changes.
FOLLOW_OFFSET = (0.0, 7.0, 52.0)
FOLLOW_LOOKAT = (-2.0, 1.5, 78.0)

PASSENGERS = [
    (-7.6, -19.0, 0.0), (-6.4, -15.0, 0.35), (-7.9, -10.0, 0.8), (-6.2, -6.0, 1.1),
    (-7.4, -1.0, 0.4), (-6.6, 3.0, 1.6), (-7.8, 8.0, 2.1), (-6.5, 11.0, 1.3),
]

STATION_KEEP = ("cement platform", "train  shellter", "mettle bench", "bench",
                "sample vending machine", "Meta lPlates Rusted", "beem",
                "window.02", "Concrete tiles",
                # The tunnel mouth. Without these the terrain hill just reads as solid rock
                # with the track running into it.
                "train tunnel")
TERRAIN_ANCHORS = [1294392831, 1294392834, 1294392833, 1294392832]


# ---------------------------------------------------------------- helpers

def f(v):
    v = float(v)
    return str(int(v)) if v == int(v) else repr(round(v, 7))


def look_rotation(fwd, up=(0.0, 1.0, 0.0)):
    fx, fy, fz = fwd
    n = math.sqrt(fx * fx + fy * fy + fz * fz)
    fx, fy, fz = fx / n, fy / n, fz / n
    ux, uy, uz = up
    rx, ry, rz = uy * fz - uz * fy, uz * fx - ux * fz, ux * fy - uy * fx
    n = math.sqrt(rx * rx + ry * ry + rz * rz)
    rx, ry, rz = rx / n, ry / n, rz / n
    ux, uy, uz = fy * rz - fz * ry, fz * rx - fx * rz, fx * ry - fy * rx
    m00, m01, m02, m10, m11, m12, m20, m21, m22 = rx, ux, fx, ry, uy, fy, rz, uz, fz
    t = m00 + m11 + m22
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        w, x, y, z = 0.25 * s, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2
        w, x, y, z = (m21 - m12) / s, 0.25 * s, (m01 + m10) / s, (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2
        w, x, y, z = (m02 - m20) / s, (m01 + m10) / s, 0.25 * s, (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2
        w, x, y, z = (m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, 0.25 * s
    return (x, y, z, w)


def euler_from_quat(q):
    x, y, z, w = q
    sp = max(-1.0, min(1.0, 2 * (w * x - y * z)))
    d = 180.0 / math.pi
    return (math.asin(sp) * d,
            math.atan2(2 * (w * y + x * z), 1 - 2 * (x * x + y * y)) * d,
            math.atan2(2 * (w * z + x * y), 1 - 2 * (x * x + z * z)) * d)


def split_blocks(text):
    """Returns (header, [(classid, anchor, stripped, body)], roots_block)."""
    idx = text.index("--- !u!")
    head, rest = text[:idx], text[idx:]
    out = []
    for m in re.finditer(r"^--- !u!(\d+) &(-?\d+)( stripped)?\n(.*?)(?=^--- |\Z)",
                         rest, re.M | re.S):
        out.append((int(m.group(1)), int(m.group(2)), bool(m.group(3)), m.group(4)))
    return head, out


def render(cid, anchor, stripped, body):
    return "--- !u!%d &%d%s\n%s" % (cid, anchor, " stripped" if stripped else "", body)


class Ids:
    def __init__(self, used):
        self.used = set(used)
        self.n = 2300000000

    def new(self):
        while self.n in self.used:
            self.n += 13
        self.used.add(self.n)
        self.n += 13
        return self.n - 13


# ---------------------------------------------------------------- pack extraction

def station_and_terrain(ids):
    """Literal blocks for the station cluster and terrain, re-anchored."""
    src = open(PACK, encoding="utf-8").read()
    _, blocks = split_blocks(src)
    by_anchor = {a: (c, s, b) for c, a, s, b in blocks}

    out, roots = [], []

    # Station: every prefab instance whose name starts with one of the keep prefixes.
    for cid, anchor, stripped, body in blocks:
        if cid != 1001:
            continue
        nm = re.search(r"propertyPath: m_Name\n\s+value: (.*)", body)
        name = nm.group(1).strip().strip("'") if nm else ""
        if not any(name.startswith(k) for k in STATION_KEEP):
            continue
        a = ids.new()
        out.append(render(1001, a, False, body))
        roots.append(a)

    # Terrain: GameObject + Transform + Terrain + TerrainCollider, references remapped.
    remap = {old: ids.new() for old in TERRAIN_ANCHORS}
    for old in TERRAIN_ANCHORS:
        cid, stripped, body = by_anchor[old]
        for o, n in remap.items():
            body = re.sub(r"\{fileID: %d\}" % o, "{fileID: %d}" % n, body)
        out.append(render(cid, remap[old], stripped, body))
    roots.append(remap[1294392834])          # the terrain's transform is a scene root

    return out, roots


# ---------------------------------------------------------------- emitters

def go_block(a, name, comps, active=True, tag="Untagged"):
    c = "\n".join("  - component: {fileID: %d}" % x for x in comps)
    return render(1, a, False, """GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
%s
  m_Layer: 0
  m_Name: %s
  m_TagString: %s
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: %d
""" % (c, name, tag, 1 if active else 0))


def tr_block(a, go, pos, children, father, rot=(0, 0, 0, 1), scale=(1, 1, 1), euler=(0, 0, 0)):
    kids = ("  m_Children:\n" + "\n".join("  - {fileID: %d}" % k for k in children)
            if children else "  m_Children: []")
    return render(4, a, False, """Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  serializedVersion: 2
  m_LocalRotation: {x: %s, y: %s, z: %s, w: %s}
  m_LocalPosition: {x: %s, y: %s, z: %s}
  m_LocalScale: {x: %s, y: %s, z: %s}
  m_ConstrainProportionsScale: 0
%s
  m_Father: {fileID: %d}
  m_LocalEulerAnglesHint: {x: %s, y: %s, z: %s}
""" % (go, f(rot[0]), f(rot[1]), f(rot[2]), f(rot[3]),
       f(pos[0]), f(pos[1]), f(pos[2]), f(scale[0]), f(scale[1]), f(scale[2]),
       kids, father, f(euler[0]), f(euler[1]), f(euler[2])))


def mono_block(a, go, guid, body):
    return render(114, a, False, """MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {fileID: 11500000, guid: %s, type: 3}
  m_Name:
  m_EditorClassIdentifier:
%s
""" % (go, guid, body.rstrip()))


def camera_block(a, go, enabled, fov=55.0):
    return render(20, a, False, """Camera:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Enabled: %d
  serializedVersion: 2
  m_ClearFlags: 1
  m_BackGroundColor: {r: 0.19215687, g: 0.3019608, b: 0.4745098, a: 0}
  m_projectionMatrixMode: 1
  m_GateFitMode: 2
  m_FOVAxisMode: 0
  m_Iso: 200
  m_ShutterSpeed: 0.005
  m_Aperture: 16
  m_FocusDistance: 10
  m_FocalLength: 50
  m_BladeCount: 5
  m_Curvature: {x: 2, y: 11}
  m_BarrelClipping: 0.25
  m_Anamorphism: 0
  m_SensorSize: {x: 36, y: 24}
  m_LensShift: {x: 0, y: 0}
  m_NormalizedViewPortRect:
    serializedVersion: 2
    x: 0
    y: 0
    width: 1
    height: 1
  near clip plane: 0.15
  far clip plane: 600
  field of view: %s
  orthographic: 0
  orthographic size: 5
  m_Depth: -1
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingPath: -1
  m_TargetTexture: {fileID: 0}
  m_TargetDisplay: 0
  m_TargetEye: 3
  m_HDR: 1
  m_AllowMSAA: 1
  m_AllowDynamicResolution: 0
  m_ForceIntoRT: 0
  m_OcclusionCulling: 1
  m_StereoConvergence: 10
  m_StereoSeparation: 0.022
""" % (go, 1 if enabled else 0, f(fov)))


def mesh_filter_block(a, go, mesh):
    return render(33, a, False, """MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Mesh: {fileID: %d, guid: %s, type: 0}
""" % (go, mesh, MESH))


def mesh_renderer_block(a, go, mat):
    return render(23, a, False, """MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Enabled: 1
  m_CastShadows: 1
  m_ReceiveShadows: 1
  m_DynamicOccludee: 1
  m_StaticShadowCaster: 0
  m_MotionVectors: 1
  m_LightProbeUsage: 1
  m_ReflectionProbeUsage: 1
  m_RayTracingMode: 2
  m_RayTraceProcedural: 0
  m_RayTracingAccelStructBuildFlagsOverride: 0
  m_RayTracingAccelStructBuildFlags: 1
  m_SmallMeshCulling: 1
  m_ForceMeshLod: -1
  m_MeshLodSelectionBias: 0
  m_RenderingLayerMask: 1
  m_RendererPriority: 0
  m_Materials:
  - {fileID: 2100000, guid: %s, type: 2}
  m_StaticBatchInfo:
    firstSubMesh: 0
    subMeshCount: 0
  m_StaticBatchRoot: {fileID: 0}
  m_ProbeAnchor: {fileID: 0}
  m_LightProbeVolumeOverride: {fileID: 0}
  m_ScaleInLightmap: 1
  m_ReceiveGI: 1
  m_PreserveUVs: 0
  m_IgnoreNormalsForChartDetection: 0
  m_ImportantGI: 0
  m_StitchLightmapSeams: 1
  m_SelectedEditorRenderState: 3
  m_MinimumChartSize: 4
  m_AutoUVMaxDistance: 0.5
  m_AutoUVMaxAngle: 89
  m_LightmapParameters: {fileID: 0}
  m_GlobalIlluminationMeshLod: 0
  m_SortingLayerID: 0
  m_SortingLayer: 0
  m_SortingOrder: 0
  m_MaskInteraction: 0
  m_AdditionalVertexStreams: {fileID: 0}
""" % (go, mat))


def box_trigger_block(a, go, size):
    return render(65, a, False, """BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Material: {fileID: 0}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 1
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {x: %s, y: %s, z: %s}
  m_Center: {x: 0, y: 0, z: 0}
""" % (go, f(size[0]), f(size[1]), f(size[2])))


def prefab_instance_block(a, guid, go_target, tr_target, name, pos, added=None,
                          tag=None, extra_mods=None):
    mods = []

    def mod(t, path, val, ref=None):
        mods.append("    - target: {fileID: %d, guid: %s, type: 3}\n"
                    "      propertyPath: %s\n      value: %s\n"
                    "      objectReference: %s" % (t, guid, path, val, ref or "{fileID: 0}"))

    mod(go_target, "m_Name", name)
    if tag:
        mod(go_target, "m_TagString", tag)
    for ax, v in zip("xyz", pos):
        mod(tr_target, "m_LocalPosition." + ax, f(v))
    for ax, v in zip("xyzw", (0, 0, 0, 1)):
        mod(tr_target, "m_LocalRotation." + ax, f(v))
    for ax in "xyz":
        mod(tr_target, "m_LocalEulerAnglesHint." + ax, "0")

    for t, path, val, ref in (extra_mods or []):
        mod(t, path, val, ref)

    ac = ("    m_AddedComponents:\n" + "\n".join(
        "    - targetCorrespondingSourceObject: {fileID: %d, guid: %s, type: 3}\n"
        "      insertIndex: -1\n      addedObject: {fileID: %d}" % (go_target, guid, x)
        for x in added)) if added else "    m_AddedComponents: []"

    return render(1001, a, False, """PrefabInstance:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Modification:
    serializedVersion: 3
    m_TransformParent: {fileID: 0}
    m_Modifications:
%s
    m_RemovedComponents: []
    m_RemovedGameObjects: []
    m_AddedGameObjects: []
%s
  m_SourcePrefab: {fileID: 100100000, guid: %s, type: 3}
""" % ("\n".join(mods), ac, guid))


def rigidbody_block(a, go):
    return render(54, a, False, """Rigidbody:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  serializedVersion: 4
  m_Mass: 1
  m_Drag: 0
  m_AngularDrag: 0.05
  m_CenterOfMass: {x: 0, y: 0, z: 0}
  m_InertiaTensor: {x: 1, y: 1, z: 1}
  m_InertiaRotation: {x: 0, y: 0, z: 0, w: 1}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ImplicitCom: 1
  m_ImplicitTensor: 1
  m_UseGravity: 0
  m_IsKinematic: 1
  m_Interpolate: 0
  m_Constraints: 0
  m_CollisionDetection: 0
""" % go)


def box_collider_block(a, go, size, center):
    return render(65, a, False, """BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Material: {fileID: 0}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 0
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {x: %s, y: %s, z: %s}
  m_Center: {x: %s, y: %s, z: %s}
""" % (go, f(size[0]), f(size[1]), f(size[2]), f(center[0]), f(center[1]), f(center[2])))


def stripped_block(a, cid, kind, source, guid, instance):
    return render(cid, a, True, """%s:
  m_CorrespondingSourceObject: {fileID: %d, guid: %s, type: 3}
  m_PrefabInstance: {fileID: %d}
  m_PrefabAsset: {fileID: 0}
""" % (kind, source, guid, instance))


# ---------------------------------------------------------------- scene model

def pristine_scene1():
    """His SampleScene as committed. Read from git so that re-running the generator never
    layers changes on top of a scene it already modified."""
    import subprocess
    try:
        out = subprocess.run(["git", "-C", REPO, "show",
                              "origin/main:Assets/Scenes/SampleScene.unity"],
                             capture_output=True, check=True)
        return out.stdout.decode("utf-8")
    except Exception as e:
        raise SystemExit("cannot read his pristine scene from git: %s" % e)


class Scene:
    def __init__(self, path, text=None):
        text = text if text is not None else open(path, encoding="utf-8").read()
        self.head, blocks = split_blocks(text)
        self.blocks = []
        self.roots = []
        for cid, a, s, b in blocks:
            if cid == 1660057539:
                self.roots = [int(x) for x in re.findall(r"- \{fileID: (-?\d+)\}", b)]
                continue
            self.blocks.append([cid, a, s, b])
        self.ids = Ids(a for _, a, _, _ in blocks)

    # -- lookups -------------------------------------------------
    def find_go(self, name):
        for cid, a, s, b in self.blocks:
            if cid == 1 and not s:
                m = re.search(r"m_Name: (.*)", b)
                if m and m.group(1).strip() == name:
                    return a
        return None

    def block(self, anchor):
        for row in self.blocks:
            if row[1] == anchor:
                return row
        return None

    def components_of(self, go):
        row = self.block(go)
        return [int(x) for x in re.findall(r"- component: \{fileID: (-?\d+)\}", row[3])]

    def component_of_type(self, go, cid):
        for c in self.components_of(go):
            r = self.block(c)
            if r and r[0] == cid:
                return c
        return None

    def prefab_instance_named(self, name):
        for cid, a, s, b in self.blocks:
            if cid == 1001:
                m = re.search(r"propertyPath: m_Name\n\s+value: (.*)", b)
                if m and m.group(1).strip() == name:
                    return a
        return None

    # -- mutations -----------------------------------------------
    def add(self, block_text):
        m = re.match(r"--- !u!(\d+) &(-?\d+)( stripped)?\n(.*)", block_text, re.S)
        self.blocks.append([int(m.group(1)), int(m.group(2)), bool(m.group(3)), m.group(4)])

    def set_active(self, go, active):
        row = self.block(go)
        row[3] = re.sub(r"m_IsActive: \d", "m_IsActive: %d" % (1 if active else 0), row[3])

    def set_material(self, go, guid):
        mr = self.component_of_type(go, 23)
        row = self.block(mr)
        row[3] = re.sub(r"m_Materials:\n  - \{fileID: \d+, guid: \w+, type: \d\}",
                        "m_Materials:\n  - {fileID: 2100000, guid: %s, type: 2}" % guid,
                        row[3])

    def add_component_to_go(self, go, comp):
        row = self.block(go)
        row[3] = re.sub(r"(  m_Component:\n(?:  - component: \{fileID: -?\d+\}\n)+)",
                        r"\1  - component: {fileID: %d}\n" % comp, row[3], count=1)

    def rename(self, go, new):
        row = self.block(go)
        row[3] = re.sub(r"m_Name: .*", "m_Name: " + new, row[3], count=1)

    def drop_collider(self, go):
        """Remove non-trigger colliders from a GameObject (signal lamps are in the way)."""
        comps = self.components_of(go)
        for c in comps:
            r = self.block(c)
            if r and r[0] in (65, 135, 136) and "m_IsTrigger: 1" not in r[3]:
                self.blocks.remove(r)
                row = self.block(go)
                row[3] = row[3].replace("  - component: {fileID: %d}\n" % c, "")

    def write(self, path):
        parts = [self.head]
        for cid, a, s, b in self.blocks:
            parts.append(render(cid, a, s, b))
        parts.append("--- !u!1660057539 &9223372036854775807\nSceneRoots:\n"
                     "  m_ObjectHideFlags: 0\n  m_Roots:\n"
                     + "\n".join("  - {fileID: %d}" % r for r in self.roots) + "\n")
        open(path, "w", encoding="utf-8", newline="\n").write("".join(parts))


# ---------------------------------------------------------------- signal building

LAMPS = [("Sphere", 0.37427998, MESH_SPHERE), ("Sphere (1)", -0.12572002, MESH_SPHERE),
         ("Sphere (2)", -0.6257199, MESH_SPHERE)]


def build_signal(sc, name, pos, red_on, yellow_on):
    """A clone of his signal group: pole, plate and three lamps."""
    tr = sc.ids.new()
    kids, lamp_go = [], {}
    parts = [("Cylinder", (0.22247982, -2.44572, 0.07611084),
              (0.16854249, 1.6453941, 0.16854249), MESH_CYLINDER, MAT_DARK, True),
             ("Cube", (0.28247976, -0.08572006, 0.063),
              (0.57574, 1.6148355, 0.23222472), MESH_CUBE, MAT_DARK, True),
             ("Sphere", (0.32247972, 0.37427998, -0.027000427),
              (0.35476,) * 3, MESH_SPHERE, MAT_RED, red_on),
             ("Sphere (1)", (0.32247972, -0.12572002, -0.027000427),
              (0.35476,) * 3, MESH_SPHERE, MAT_YELLOW, yellow_on),
             ("Sphere (2)", (0.32247972, -0.6257199, -0.027000427),
              (0.35476,) * 3, MESH_SPHERE, MAT_GREEN, False)]
    for nm, lp, ls, mesh, mat, on in parts:
        t, g = sc.ids.new(), sc.ids.new()
        mf, mr = sc.ids.new(), sc.ids.new()
        sc.add(go_block(g, nm, [t, mf, mr], active=on))
        sc.add(tr_block(t, g, lp, [], tr, scale=ls))
        sc.add(mesh_filter_block(mf, g, mesh))
        sc.add(mesh_renderer_block(mr, g, mat))
        kids.append(t)
        lamp_go[nm] = g
    g = sc.ids.new()
    sc.add(go_block(g, name, [tr]))
    sc.add(tr_block(tr, g, pos, kids, 0, scale=(SIGNAL_SCALE,) * 3))
    sc.roots.append(tr)
    return lamp_go


# ---------------------------------------------------------------- train patching

def patch_train_instance(sc, anchor, z, added, tag=None):
    """Rewrite his train prefab instance: new z, optional tag, and added components."""
    row = sc.block(anchor)
    body = row[3]

    body = re.sub(
        r"(target: \{fileID: %d, guid: %s, type: 3\}\n\s+propertyPath: m_LocalPosition\.z\n\s+value: )\S+"
        % (TRAIN_TR, TRAIN_GUID), r"\g<1>" + f(z), body)

    if tag and "m_TagString" not in body:
        body = body.replace(
            "    m_RemovedComponents: []",
            "    - target: {fileID: %d, guid: %s, type: 3}\n"
            "      propertyPath: m_TagString\n      value: %s\n"
            "      objectReference: {fileID: 0}\n"
            "    m_RemovedComponents: []" % (TRAIN_GO, TRAIN_GUID, tag), 1)

    ac = "\n".join(
        "    - targetCorrespondingSourceObject: {fileID: %d, guid: %s, type: 3}\n"
        "      insertIndex: -1\n      addedObject: {fileID: %d}" % (TRAIN_GO, TRAIN_GUID, x)
        for x in added)
    body = body.replace("    m_AddedComponents: []",
                        "    m_AddedComponents:\n" + ac, 1)
    row[3] = body


def hide_catenary_over_signal(sc, signal_z):
    """The rail prefab carries an overhead catenary, and one of its gantries stands directly in
    front of the signal from the driving camera, which makes the light hard to read. Switch the
    wires off on just the segment that spans the signal; the rest of the line keeps them."""
    hidden = 0
    pattern = (r"target: \{fileID: " + str(RAIL_TR) + ", guid: " + RAIL_GUID +
               r", type: 3\}\n\s+propertyPath: m_LocalPosition\.z\n\s+value: (\S+)")

    for row in sc.blocks:
        if row[0] != 1001 or RAIL_GUID not in row[3]:
            continue

        m = re.search(pattern, row[3])

        if not m:
            continue

        z = float(m.group(1))

        if not (z - RAIL_SEGMENT_LENGTH <= signal_z <= z):
            continue

        if ("fileID: " + str(RAIL_WIRE_GO)) in row[3]:
            continue

        mod = ("    - target: {fileID: " + str(RAIL_WIRE_GO) + ", guid: " + RAIL_GUID +
               ", type: 3}\n"
               "      propertyPath: m_IsActive\n"
               "      value: 0\n"
               "      objectReference: {fileID: 0}\n"
               "    m_RemovedComponents: []")

        row[3] = row[3].replace("    m_RemovedComponents: []", mod, 1)
        hidden += 1

    if hidden == 0:
        print("  WARNING: no rail segment spans the signal; catenary left alone")

    return hidden


def paint_his_signal(sc, red_on, yellow_on, green_on):
    """His signal lamps carry the default material; give them colours and states."""
    for nm, mat, on in (("Sphere", MAT_RED, red_on),
                        ("Sphere (1)", MAT_YELLOW, yellow_on),
                        ("Sphere (2)", MAT_GREEN, green_on),
                        ("Cube", MAT_DARK, True),
                        ("Cylinder", MAT_DARK, True)):
        g = sc.find_go(nm)
        if g is None:
            raise SystemExit("signal part missing from his scene: " + nm)
        sc.set_material(g, mat)
        sc.set_active(g, on)
        sc.drop_collider(g)
    return {n: sc.find_go(n) for n in ("Sphere", "Sphere (1)", "Sphere (2)")}


def add_station(sc):
    blocks, roots = station_and_terrain(sc.ids)
    for b in blocks:
        sc.add(b)
    sc.roots.extend(roots)


def add_empty(sc, name, pos):
    t, g = sc.ids.new(), sc.ids.new()
    sc.add(go_block(g, name, [t]))
    sc.add(tr_block(t, g, pos, [], 0))
    sc.roots.append(t)
    return t, g


# ---------------------------------------------------------------- scene 1

def build_scene1(his_guids):
    sc = Scene(SCENE1_SRC, pristine_scene1())

    lamps = paint_his_signal(sc, red_on=True, yellow_on=False, green_on=False)
    hide_catenary_over_signal(sc, SIGNAL_POS_Z)

    stop_tr, _ = add_empty(sc, "StationStopWaypoint", (TRAIN_X, TRAIN_Y, TRAIN_STOP_Z))
    end_tr, _ = add_empty(sc, "EndOfTrackStopPoint", (TRAIN_X, TRAIN_Y, END_OF_TRACK_Z))

    # Approach signal: starts yellow, his Signal1Trigger flips it to red as the train passes.
    ap = build_signal(sc, "Signal 1 (approach)", APPROACH_SIGNAL_POS,
                      red_on=False, yellow_on=True)

    train_inst = sc.prefab_instance_named("train")
    train_go = sc.ids.new()
    train_tr = sc.ids.new()
    brake_id = sc.ids.new()
    loader_id = sc.ids.new()
    rb_id = sc.ids.new()
    col_id = sc.ids.new()

    patch_train_instance(sc, train_inst, TRAIN_START_Z,
                         [rb_id, col_id, brake_id, loader_id], tag="Train")
    sc.add(stripped_block(train_go, 1, "GameObject", TRAIN_GO, TRAIN_GUID, train_inst))
    sc.add(stripped_block(train_tr, 4, "Transform", TRAIN_TR, TRAIN_GUID, train_inst))

    # Without a collider and a kinematic body the train passes straight through the trigger
    # and his Signal1Trigger never fires. Bounds come from the probe: 2.66 x 4.65 x 122.16.
    sc.add(rigidbody_block(rb_id, train_go))
    sc.add(box_collider_block(col_id, train_go, (2.66, 4.65, 122.16), (0, 2.25, -0.17)))

    # His brake script. lastSignal fields stay empty: scene 2 owns the ten seconds.
    sc.add(mono_block(brake_id, train_go, his_guids["TrainStationButtonStop"], """  stationStopWaypoint: {fileID: %d}
  endOfTrackStopPoint: {fileID: %d}
  maxSpeed: 15
  maxDeceleration: 5
  lastSignalRedLight: {fileID: 0}
  lastSignalGreenLight: {fileID: 0}
  greenLightDelay: 10""" % (stop_tr, end_tr)))

    sc.add(mono_block(loader_id, train_go, SCRIPTS["ArriveAtStationLoader"], """  stationStopWaypoint: {fileID: %d}
  arriveDistance: 0.5
  stationarySpeed: 0.05
  settleTime: 0.75
  nextSceneName: Scene2_StationBoarding
  loadDelay: 0.5""" % stop_tr))

    # Trigger across the track at the approach signal.
    tt, tg = sc.ids.new(), sc.ids.new()
    box, trig = sc.ids.new(), sc.ids.new()
    sc.add(go_block(tg, "Signal 1 Trigger", [tt, box, trig]))
    sc.add(tr_block(tt, tg, (0, 3, APPROACH_SIGNAL_Z), [], 0))
    sc.add(box_trigger_block(box, tg, (24, 10, 2)))
    sc.add(mono_block(trig, tg, his_guids["Signal1Trigger"],
                      "  redLight: {fileID: %d}\n  yellowLight: {fileID: %d}"
                      % (ap["Sphere"], ap["Sphere (1)"])))
    sc.roots.append(tt)

    # Follow camera on his Main Camera.
    cam_go = sc.find_go("Main Camera")
    follow = sc.ids.new()
    sc.add(mono_block(follow, cam_go, SCRIPTS["TrainFollowCamera"], """  target: {fileID: %d}
  localOffset: {x: %s, y: %s, z: %s}
  lookAtOffset: {x: %s, y: %s, z: %s}
  followSmoothing: 4
  snapOnStart: 1""" % (train_tr, f(FOLLOW_OFFSET[0]), f(FOLLOW_OFFSET[1]), f(FOLLOW_OFFSET[2]),
                       f(FOLLOW_LOOKAT[0]), f(FOLLOW_LOOKAT[1]), f(FOLLOW_LOOKAT[2]))))
    sc.add_component_to_go(cam_go, follow)

    add_station(sc)
    sc.write(SCENE1_OUT)
    return sc


# ---------------------------------------------------------------- scene 2

def build_scene2(his_guids):
    sc = Scene(SCENE1_SRC, pristine_scene1())   # his scene again: same lighting, rails, light, signal

    lamps = paint_his_signal(sc, red_on=True, yellow_on=False, green_on=False)

    hide_catenary_over_signal(sc, SIGNAL_POS_Z)

    # The approach signal is already red by the time we get here.
    build_signal(sc, "Signal 1 (approach)", APPROACH_SIGNAL_POS,
                 red_on=True, yellow_on=False)

    stop_tr, _ = add_empty(sc, "StationStopWaypoint", (TRAIN_X, TRAIN_Y, TRAIN_STOP_Z))

    train_inst = sc.prefab_instance_named("train")
    train_go, train_tr = sc.ids.new(), sc.ids.new()
    drive_id = sc.ids.new()
    patch_train_instance(sc, train_inst, TRAIN_STOP_Z, [drive_id], tag="Train")
    sc.add(stripped_block(train_go, 1, "GameObject", TRAIN_GO, TRAIN_GUID, train_inst))
    sc.add(stripped_block(train_tr, 4, "Transform", TRAIN_TR, TRAIN_GUID, train_inst))
    sc.add(mono_block(drive_id, train_go, SCRIPTS["TrainSpaceDrive"], """  maxSpeed: 15
  acceleration: 3
  deceleration: 5
  controlEnabled: 0
  startMoving: 0"""))

    # His Main Camera becomes the train camera: it already carries the audio listener.
    cam_go = sc.find_go("Main Camera")
    sc.rename(cam_go, "Cam_Train")
    cam_component = sc.component_of_type(cam_go, 20)
    sc.block(cam_component)[3] = re.sub(r"m_Enabled: 1", "m_Enabled: 0",
                                        sc.block(cam_component)[3], count=1)
    follow = sc.ids.new()
    sc.add(mono_block(follow, cam_go, SCRIPTS["TrainFollowCamera"], """  target: {fileID: %d}
  localOffset: {x: %s, y: %s, z: %s}
  lookAtOffset: {x: %s, y: %s, z: %s}
  followSmoothing: 4
  snapOnStart: 1""" % (train_tr, f(FOLLOW_OFFSET[0]), f(FOLLOW_OFFSET[1]), f(FOLLOW_OFFSET[2]),
                       f(FOLLOW_LOOKAT[0]), f(FOLLOW_LOOKAT[1]), f(FOLLOW_LOOKAT[2]))))
    sc.add_component_to_go(cam_go, follow)
    # Park it where the follow script will hold it, so frame one is already right.
    cam_tr = sc.component_of_type(cam_go, 4)
    cpos = (TRAIN_X + FOLLOW_OFFSET[0], TRAIN_Y + FOLLOW_OFFSET[1], TRAIN_STOP_Z + FOLLOW_OFFSET[2])
    ctgt = (TRAIN_X + FOLLOW_LOOKAT[0], TRAIN_Y + FOLLOW_LOOKAT[1], TRAIN_STOP_Z + FOLLOW_LOOKAT[2])
    q = look_rotation(tuple(ctgt[i] - cpos[i] for i in range(3)))
    e = euler_from_quat(q)
    r = sc.block(cam_tr)
    r[3] = re.sub(r"m_LocalRotation: \{[^}]*\}",
                  "m_LocalRotation: {x: %s, y: %s, z: %s, w: %s}" % tuple(f(v) for v in q), r[3])
    r[3] = re.sub(r"m_LocalPosition: \{[^}]*\}",
                  "m_LocalPosition: {x: %s, y: %s, z: %s}" % tuple(f(v) for v in cpos), r[3])
    r[3] = re.sub(r"m_LocalEulerAnglesHint: \{[^}]*\}",
                  "m_LocalEulerAnglesHint: {x: %s, y: %s, z: %s}" % tuple(f(v) for v in e), r[3])

    # Station shots.
    cams = {"Cam_Train": cam_component}
    for name, pos, tgt, on in SHOTS:
        q = look_rotation(tuple(tgt[i] - pos[i] for i in range(3)))
        t, g, c = sc.ids.new(), sc.ids.new(), sc.ids.new()
        sc.add(go_block(g, name, [t, c]))
        sc.add(tr_block(t, g, pos, [], 0, rot=q, euler=euler_from_quat(q)))
        sc.add(camera_block(c, g, on))
        sc.roots.append(t)
        cams[name] = c

    # Passengers and their paths.
    for i, (sx, sz, delay) in enumerate(PASSENGERS):
        door_z = TRAIN_STOP_Z + DOOR_LOCAL_Z[i % len(DOOR_LOCAL_Z)]
        qt, qg = add_empty(sc, "Queue %d" % (i + 1), (PLATFORM_X + 1.4, PLATFORM_TOP_Y, door_z))
        dt, dg = add_empty(sc, "Door %d" % (i + 1), (DOOR_LINE_X, PLATFORM_TOP_Y, door_z))
        walker = sc.ids.new()
        inst = sc.ids.new()
        sc.add(prefab_instance_block(
            inst, PERSON_GUID, PERSON_GO, PERSON_TR,
            "Passenger %d" % (i + 1),
            (sx, PLATFORM_TOP_Y, sz), added=[walker],
            extra_mods=[
                (PERSON_ANIMATOR, "m_Controller", "",
                 "{fileID: 9100000, guid: %s, type: 2}" % PERSON_CONTROLLER),
                # The clip is In Place, so the walker keeps control of where she actually goes.
                (PERSON_ANIMATOR, "m_ApplyRootMotion", "0", None),
            ]))
        sc.roots.append(inst)
        pgo = sc.ids.new()
        sc.add(stripped_block(pgo, 1, "GameObject", PERSON_GO, PERSON_GUID, inst))
        sc.add(mono_block(walker, pgo, SCRIPTS["PassengerWalker"], """  waypoints:
  - {fileID: %d}
  - {fileID: %d}
  moveSpeed: %s
  turnSpeed: 6
  startDelay: %s
  arriveDistance: 0.15
  deactivateOnArrival: 1
  boardDelay: 0.2
  enableBoneWalk: 0
  stepFrequency: 2.2
  legSwingAngle: 26
  armSwingAngle: 16
  swingAxis: {x: 1, y: 0, z: 0}
  bobHeight: 0.035""" % (qt, dt, f(1.25 + (i % 3) * 0.12), f(delay))))

    # Director.
    dt, dg = sc.ids.new(), sc.ids.new()
    director = sc.ids.new()
    sc.add(go_block(dg, "Scene2Director", [dt, director]))
    sc.add(tr_block(dt, dg, (0, 0, 0), [], 0))
    sc.add(mono_block(director, dg, SCRIPTS["Scene2Director"], """  stationCameraA: {fileID: %d}
  stationCameraB: {fileID: %d}
  stationCameraC: {fileID: %d}
  shotBTime: 3.5
  shotCTime: 6.5
  trainCamera: {fileID: %d}
  cutToTrainTime: 9
  lastSignalRedLight: {fileID: %d}
  lastSignalGreenLight: {fileID: %d}
  greenLightDelay: 10
  trainDrive: {fileID: %d}
  pressSpacePrompt: {fileID: 0}
  pressSpaceLabel: {fileID: 0}
  promptFadeSpeed: 2""" % (cams["Cam_Station_A"], cams["Cam_Station_B"], cams["Cam_Station_C"],
                           cams["Cam_Train"], lamps["Sphere"], lamps["Sphere (2)"], drive_id)))
    sc.roots.append(dt)

    add_station(sc)
    sc.write(SCENE2_OUT)
    return sc


# ---------------------------------------------------------------- main

def his_script_guids():
    out = {}
    for n in ("TrainStationButtonStop", "Signal1Trigger"):
        p = os.path.join(REPO, "Assets", n + ".cs.meta")
        out[n] = re.search(r"guid: (\w{32})", open(p, encoding="utf-8").read()).group(1)
    return out


def add_train_tag():
    p = os.path.join(REPO, "ProjectSettings", "TagManager.asset")
    s = open(p, encoding="utf-8").read()
    if "- Train" in s:
        return False
    s = s.replace("  tags: []", "  tags:\n  - Train", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    return True


if __name__ == "__main__":
    g = his_script_guids()
    print("his script guids:", g)
    print("Train tag added:", add_train_tag())
    s2 = build_scene2(g)         # from his pristine scene, before scene 1 is overwritten
    print("scene 2 written:", SCENE2_OUT)
    s1 = build_scene1(g)
    print("scene 1 written:", SCENE1_OUT)
