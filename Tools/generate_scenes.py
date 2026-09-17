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
SCENE3_OUT = os.path.join(REPO, "Assets", "Scenes", "Scene3_Crossover.unity")
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

MAT_RED = "aca046793e216e037c2e01a580e9127f"      # Materials/Signal Red.mat, emissive
MAT_YELLOW = "170f3d89319b2840119add65eda2157d"   # Materials/Signal Yellow.mat, emissive
MAT_DARK = "9fa6d9495e43248479959c8c53531c6e"     # New Material 2.mat

MESH = "0000000000000000e000000000000000"
MESH_CUBE, MESH_CYLINDER, MESH_SPHERE = 10202, 10206, 10207


def guid_for(p):
    return hashlib.md5(("train_sim::" + p).encode()).hexdigest()


MAT_GREEN = guid_for("Assets/Materials/Signal Green.mat")
SCRIPTS = {n: guid_for("Assets/" + n + ".cs") for n in
           ("Scene2Director", "PassengerWalker", "TrainSpaceDrive",
            "TrainFollowCamera", "ArriveAtStationLoader",
            "TrainDoor", "TrainWheels", "PassengerVariety", "TrainAudio", "Scene1Hud",
            "Scene3Director", "TrainPathFollower", "TrainTint", "TunnelExitLoader")}
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

# Measured with Tools > Train Sim > Probe Layout rather than guessed. The old numbers put
# passengers off the south end of the deck and their door point out over the track, which is
# why they appeared to walk on air.
PLATFORM_X_MIN, PLATFORM_X_MAX = -11.92, -4.80
PLATFORM_Z_MIN, PLATFORM_Z_MAX = -10.66, 13.75
PLATFORM_TOP_Y = 2.036
PASSENGER_FEET_Y = 2.156      # deck plus the 0.12 the Mixamo root sits above the lowest vertex
PLATFORM_X = PLATFORM_X_MIN

CARRIAGE_SIDE_X = -3.73       # where the carriage skin is, from the probe
QUEUE_X = -6.0                # well inside the deck
EDGE_X = -4.9                 # the last step still on the platform
INSIDE_X = -3.2               # through the doorway, inside the carriage

TRAIN_BODY_MAT = "bd5a2dc97bddbfb4bb14ebf097929d60"
DOOR_Y = 3.04                 # panels span roughly deck height to 4.0
DOOR_LOCAL_Z_WORLD = [-9.0, -3.0, 3.0, 9.0]   # all inside the platform z range


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

# Spawn x and z, start delay, and which door they head for. Every spawn is inside the deck
# bounds above.
PASSENGERS = [
    (-9.8, -8.0, 0.0, 0), (-7.4, -6.5, 0.5, 0),
    (-10.4, -2.0, 0.9, 1), (-7.9, -0.5, 1.4, 1),
    (-9.2, 4.5, 0.3, 2), (-7.1, 6.0, 1.8, 2),
    (-10.1, 10.5, 2.2, 3), (-7.6, 12.0, 1.1, 3),
]

# ---------------------------------------------------------------- scene 3 layout
#
# Measured with a batch-mode probe on 2026-09-17:
#   - every rail piece is double track, centres x = -2.4 (west, ours) and x = +2.4 (east)
#   - the pack terrain ends at z = 97.9, just past the tunnel hill, so scene 3 stands on
#     Scene3_NorthTerrain.asset (Tools > Train Sim > Build Scene 3 Ground), z 97.9 .. 497.9
#   - the train pivot sits 60.91 behind its nose and 61.24 ahead of its tail
#   - the pack's curve pieces are 90 degree bends of radius ~100, useless as a crossover, so the
#     points are laid from primitives along the same S-bend TrainPathFollower drives

EAST_X = 2.4
TRAIN_NOSE = 60.91
TRAIN_TAIL = 61.24

SCENE3_PLAYER_START_Z = 49.1   # pivot; nose at 110, clear of the hill. Scene 2 hands over here.
SCENE3_SIGNAL_Z = 187.0        # the nose must stop short of this
CROSS_START_Z = 195.0          # south end of the crossover, on the east track
CROSS_END_Z = 245.0            # north end, on the west track
SECOND_TRAIN_START_Z = 310.9   # pivot facing south, so its nose is at 250, 5 past the points
# Facing south, the second train spans the same z as ours did at the station stop.
SECOND_TRAIN_STOP_Z = TRAIN_STOP_Z - (TRAIN_TAIL - TRAIN_NOSE)

SCENE3_BRAKING_Z = 150.0       # a point on the rail segment the player brakes along
# Fixed shot by the far platform for the arrival: the chase camera would be looking south past
# the end of the pack terrain, into empty sky.
ARRIVAL_CUT_Z = 14.0           # lead car z, the north end of the platforms
ARRIVAL_CAM = ((5.5, 3.8, 25.0), (1.0, 2.0, -40.0))   # north end of the far platform, looking along it

NORTH_TERRAIN = os.path.join(REPO, "Assets", "Scenes", "Scene3_NorthTerrain.asset")
NORTH_TERRAIN_POS = (-101, 0, 97.9)
EXTRA_RAIL_Z = (264.46, 366.22, 467.98)   # each piece covers (z - 101.76) .. z
MAT_STEEL = guid_for("Assets/Materials/Crossover Steel.mat")
MAT_SLEEPER = guid_for("Assets/Materials/Crossover Sleeper.mat")

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


def point_light_block(a, go, colour, intensity=2.4, rng=6.0):
    """A small point light on a signal lamp, so the change actually throws colour onto the pole
    and the ballast rather than being a flat swap of albedo."""
    return render(108, a, False, """Light:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Enabled: 1
  serializedVersion: 13
  m_Type: 2
  m_Color: {r: %s, g: %s, b: %s, a: 1}
  m_Intensity: %s
  m_Range: %s
  m_SpotAngle: 30
  m_InnerSpotAngle: 21.802082
  m_CookieSize2D: {x: 10, y: 10}
  m_Shadows:
    m_Type: 0
    m_Resolution: -1
    m_CustomResolution: -1
    m_Strength: 1
    m_Bias: 0.05
    m_NormalBias: 0.4
    m_NearPlane: 0.2
    m_CullingMatrixOverride:
      e00: 1
      e01: 0
      e02: 0
      e03: 0
      e10: 0
      e11: 1
      e12: 0
      e13: 0
      e20: 0
      e21: 0
      e22: 1
      e23: 0
      e30: 0
      e31: 0
      e32: 0
      e33: 1
    m_UseCullingMatrixOverride: 0
  m_Cookie: {fileID: 0}
  m_DrawHalo: 0
  m_Flare: {fileID: 0}
  m_RenderMode: 0
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingLayerMask: 1
  m_Lightmapping: 4
  m_LightShadowCasterMode: 0
  m_AreaSize: {x: 1, y: 1}
  m_BounceIntensity: 1
  m_ColorTemperature: 6570
  m_UseColorTemperature: 0
  m_BoundingSphereOverride: {x: 0, y: 0, z: 0, w: 0}
  m_UseBoundingSphereOverride: 0
  m_UseViewFrustumForShadowCasterCull: 1
  m_ForceVisible: 0
  m_ShapeRadius: 0
  m_ShadowAngle: 0
  m_LightUnit: 1
  m_LuxAtDistance: 1
  m_EnableSpotReflector: 1
""" % (go, f(colour[0]), f(colour[1]), f(colour[2]), f(intensity), f(rng)))


def prefab_instance_block(a, guid, go_target, tr_target, name, pos, added=None,
                          tag=None, extra_mods=None, rot=(0, 0, 0, 1), euler=(0, 0, 0)):
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
    for ax, v in zip("xyzw", rot):
        mod(tr_target, "m_LocalRotation." + ax, f(v))
    for ax, v in zip("xyz", euler):
        mod(tr_target, "m_LocalEulerAnglesHint." + ax, f(v))

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


WHEELS_FIELDS = '''  wheelNamePrefix: Wheel
  wheelRadius: 0.45
  spinAxis: {x: 1, y: 0, z: 0}
  manualSpeed: 0'''

AUDIO_FIELDS = '''  rumbleLoop: {fileID: 0}
  brakeSqueal: {fileID: 0}
  maxSpeed: 15
  minPitch: 0.55
  maxPitch: 1.25
  maxVolume: 0.7
  fadeSpeed: 2
  squealVolume: 0.8
  squealSpeedThreshold: 4'''

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


def build_doors(sc, train_stop_z):
    """Sliding doors on the carriage side.

    The Polyeler carriage has no door geometry at all, so each boarding point gets a pair of
    thin panels in the train's own body material, sat flush against the skin. They are what the
    passengers walk into, which is what makes the boarding read as boarding."""
    doors = []

    for i, dz in enumerate(DOOR_LOCAL_Z_WORLD):
        root_tr = sc.ids.new()
        panels = []

        for side, off in (("Left", -0.31), ("Right", 0.31)):
            t, g = sc.ids.new(), sc.ids.new()
            mf, mr = sc.ids.new(), sc.ids.new()
            sc.add(go_block(g, side + " Panel", [t, mf, mr]))
            sc.add(tr_block(t, g, (0.0, 0.0, off), [], root_tr,
                            scale=(0.12, 2.0, 0.6)))
            sc.add(mesh_filter_block(mf, g, MESH_CUBE))
            sc.add(mesh_renderer_block(mr, g, TRAIN_BODY_MAT))
            panels.append(t)

        door_mb = sc.ids.new()
        g = sc.ids.new()
        sc.add(go_block(g, "Train Door %d" % (i + 1), [root_tr, door_mb]))
        sc.add(tr_block(root_tr, g, (CARRIAGE_SIDE_X, DOOR_Y, dz), panels, 0))
        sc.add(mono_block(door_mb, g, SCRIPTS["TrainDoor"], """  leftPanel: {fileID: %d}
  rightPanel: {fileID: %d}
  openOffset: 0.62
  slideSpeed: 1.6
  startOpen: 0""" % (panels[0], panels[1])))
        sc.roots.append(root_tr)
        doors.append(door_mb)

    return doors


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
    LAMP_LIGHT = {"Sphere": (1.0, 0.15, 0.12),
                  "Sphere (1)": (1.0, 0.85, 0.1),
                  "Sphere (2)": (0.2, 1.0, 0.3)}

    for nm, lp, ls, mesh, mat, on in parts:
        t, g = sc.ids.new(), sc.ids.new()
        mf, mr = sc.ids.new(), sc.ids.new()
        comps = [t, mf, mr]

        # The lamps carry a light of their own. It switches with the lamp, so the change to
        # green lights the pole and the ballast instead of only changing the sphere colour.
        if nm in LAMP_LIGHT:
            li = sc.ids.new()
            comps.append(li)

        sc.add(go_block(g, nm, comps, active=on))
        sc.add(tr_block(t, g, lp, [], tr, scale=ls))
        sc.add(mesh_filter_block(mf, g, mesh))
        sc.add(mesh_renderer_block(mr, g, mat))

        if nm in LAMP_LIGHT:
            sc.add(point_light_block(li, g, LAMP_LIGHT[nm]))

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
    LAMP_LIGHT = {"Sphere": (1.0, 0.15, 0.12),
                  "Sphere (1)": (1.0, 0.85, 0.1),
                  "Sphere (2)": (0.2, 1.0, 0.3)}

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

        # His station signal is the one the whole sequence turns on, so its lamps get lights
        # too. They switch with the lamp, so green actually throws colour on the scene.
        if nm in LAMP_LIGHT:
            li = sc.ids.new()
            sc.add(point_light_block(li, g, LAMP_LIGHT[nm]))
            sc.add_component_to_go(g, li)
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
    wheels_id = sc.ids.new()
    audio_id = sc.ids.new()

    patch_train_instance(sc, train_inst, TRAIN_START_Z,
                         [rb_id, col_id, brake_id, loader_id, wheels_id, audio_id],
                         tag="Train")
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

    sc.add(mono_block(wheels_id, train_go, SCRIPTS["TrainWheels"], WHEELS_FIELDS))
    sc.add(mono_block(audio_id, train_go, SCRIPTS["TrainAudio"], AUDIO_FIELDS))

    # The heads up display: without it the scene never tells the player to brake, and the
    # outcome only reaches the console.
    hud_tr, hud_go = add_empty(sc, "Scene1 HUD", (0, 0, 0))
    hud_mb = sc.ids.new()
    sc.add(mono_block(hud_mb, hud_go, SCRIPTS["Scene1Hud"], """  train: {fileID: %d}
  stationStopWaypoint: {fileID: %d}
  maxSpeed: 15
  maxDeceleration: 5
  promptLead: 30
  arriveDistance: 0.6
  restartKeyName: R""" % (train_tr, stop_tr)))
    sc.add_component_to_go(hud_go, hud_mb)

    add_station(sc)
    add_north_world(sc, drive_second_train=False)
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
    wheels_id = sc.ids.new()
    audio_id = sc.ids.new()
    exit_id = sc.ids.new()
    patch_train_instance(sc, train_inst, TRAIN_STOP_Z,
                         [drive_id, wheels_id, audio_id, exit_id], tag="Train")
    sc.add(stripped_block(train_go, 1, "GameObject", TRAIN_GO, TRAIN_GUID, train_inst))
    sc.add(stripped_block(train_tr, 4, "Transform", TRAIN_TR, TRAIN_GUID, train_inst))
    sc.add(mono_block(drive_id, train_go, SCRIPTS["TrainSpaceDrive"], """  maxSpeed: 15
  acceleration: 1.2
  deceleration: 5
  controlEnabled: 0
  startMoving: 0"""))

    sc.add(mono_block(wheels_id, train_go, SCRIPTS["TrainWheels"], WHEELS_FIELDS))
    sc.add(mono_block(audio_id, train_go, SCRIPTS["TrainAudio"], AUDIO_FIELDS))

    # Out the far side of the tunnel, scene 3 takes over at the same spot and speed.
    sc.add(mono_block(exit_id, train_go, SCRIPTS["TunnelExitLoader"], """  handoverZ: %s
  nextSceneName: Scene3_Crossover""" % f(SCENE3_PLAYER_START_Z)))

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

    # Passengers and their paths. Every waypoint but the last sits on the platform deck; only
    # the final step crosses the 1.07 unit gap into the carriage.
    doors = build_doors(sc, TRAIN_STOP_Z)

    for i, (sx, sz, delay, door_index) in enumerate(PASSENGERS):
        door_z = DOOR_LOCAL_Z_WORLD[door_index]
        qt, _ = add_empty(sc, "Queue %d" % (i + 1),
                          (QUEUE_X, PASSENGER_FEET_Y, door_z))
        et, _ = add_empty(sc, "Edge %d" % (i + 1),
                          (EDGE_X, PASSENGER_FEET_Y, door_z))
        dt, _ = add_empty(sc, "Board %d" % (i + 1),
                          (INSIDE_X, PASSENGER_FEET_Y, door_z))
        walker = sc.ids.new()
        variety = sc.ids.new()
        inst = sc.ids.new()
        sc.add(prefab_instance_block(
            inst, PERSON_GUID, PERSON_GO, PERSON_TR,
            "Passenger %d" % (i + 1),
            (sx, PASSENGER_FEET_Y, sz), added=[walker, variety],
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
  - {fileID: %d}
  moveSpeed: %s
  turnSpeed: 6
  startDelay: %s
  arriveDistance: 0.15
  deactivateOnArrival: 1
  boardDelay: 0.25
  door: {fileID: %d}
  enableBoneWalk: 0
  stepFrequency: 2.2
  legSwingAngle: 26
  armSwingAngle: 16
  swingAxis: {x: 1, y: 0, z: 0}
  bobHeight: 0.035""" % (qt, et, dt, f(1.1 + (i % 4) * 0.09), f(delay),
                          doors[door_index])))

        sc.add(mono_block(variety, pgo, SCRIPTS["PassengerVariety"], """  seed: %d
  minScale: 0.94
  maxScale: 1.06
  tintClothing: 1
  tintStrength: 0.35
  offsetAnimator: 1""" % i))

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
  trainDoors:
%s
  doorsCloseTime: 8.5
  stationAmbience: {fileID: 0}
  signalChange: {fileID: 0}
  ambienceVolume: 0.35
  trainDrive: {fileID: %d}
  pressSpacePrompt: {fileID: 0}
  pressSpaceLabel: {fileID: 0}
  promptFadeSpeed: 2""" % (cams["Cam_Station_A"], cams["Cam_Station_B"], cams["Cam_Station_C"],
                           cams["Cam_Train"], lamps["Sphere"], lamps["Sphere (2)"],
        "\n".join("  - {fileID: %d}" % d for d in doors), drive_id)))
    sc.roots.append(dt)

    add_station(sc)
    add_north_world(sc, drive_second_train=False)
    sc.write(SCENE2_OUT)
    return sc


# ---------------------------------------------------------------- scene 3

MATERIAL_TEMPLATE = """%%YAML 1.1
%%TAG !u! tag:unity3d.com,2011:
--- !u!21 &2100000
Material:
  serializedVersion: 8
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_Name: %(name)s
  m_Shader: {fileID: 46, guid: 0000000000000000f000000000000000, type: 0}
  m_Parent: {fileID: 0}
  m_ModifiedSerializedProperties: 0
  m_ValidKeywords: []
  m_InvalidKeywords: []
  m_LightmapFlags: 4
  m_EnableInstancingVariants: 1
  m_DoubleSidedGI: 0
  m_CustomRenderQueue: -1
  stringTagMap: {}
  disabledShaderPasses: []
  m_LockedProperties:
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs: []
    m_Ints: []
    m_Floats:
    - _Glossiness: %(gloss)s
    - _Metallic: %(metal)s
    - _Mode: 0
    m_Colors:
    - _Color: {r: %(r)s, g: %(g)s, b: %(b)s, a: 1}
    - _EmissionColor: {r: 0, g: 0, b: 0, a: 1}
  m_BuildTextureStacks: []
  m_AllowLocking: 1
"""


def write_material(name, colour, metal, gloss):
    rel = "Assets/Materials/" + name + ".mat"
    path = os.path.join(REPO, *rel.split("/"))
    open(path, "w", encoding="utf-8", newline="\n").write(MATERIAL_TEMPLATE % {
        "name": name, "r": f(colour[0]), "g": f(colour[1]), "b": f(colour[2]),
        "metal": f(metal), "gloss": f(gloss)})
    open(path + ".meta", "w", encoding="utf-8", newline="\n").write(
        "fileFormatVersion: 2\nguid: %s\nNativeFormatImporter:\n  externalObjects: {}\n"
        "  mainObjectFileID: 2100000\n  userData: \n  assetBundleName: \n"
        "  assetBundleVariant: \n" % guid_for(rel))


def crossover_x(z):
    """Same S-bend as TrainPathFollower.XAtZ: east track at CROSS_START_Z, west at CROSS_END_Z."""
    if z >= CROSS_END_Z:
        return TRAIN_X
    if z <= CROSS_START_Z:
        return EAST_X
    u = (z - CROSS_START_Z) / (CROSS_END_Z - CROSS_START_Z)
    return (EAST_X + TRAIN_X) / 2 + (EAST_X - TRAIN_X) / 2 * math.cos(math.pi * u)


def yaw_quat(dx, dz):
    a = math.atan2(dx, dz) / 2
    return (0.0, math.sin(a), 0.0, math.cos(a)), (0.0, math.degrees(2 * a), 0.0)


def add_box(sc, parent, name, pos, rot, euler, scale, mat):
    t, g, mf, mr = sc.ids.new(), sc.ids.new(), sc.ids.new(), sc.ids.new()
    sc.add(go_block(g, name, [t, mf, mr]))
    sc.add(tr_block(t, g, pos, [], parent, rot=rot, scale=scale, euler=euler))
    sc.add(mesh_filter_block(mf, g, MESH_CUBE))
    sc.add(mesh_renderer_block(mr, g, mat))
    return t


def build_crossover(sc):
    """The points: two rails and their sleepers along the S-bend between the tracks.

    Where the bend still lies over one of the tracks its sleepers would sit inside the existing
    ones, so those are left out; the rails run the full length, a hair above the track's own, the
    way a switch blade lies against the stock rail."""
    root_t, root_g = sc.ids.new(), sc.ids.new()
    kids = []

    step = 2.0
    z = CROSS_START_Z - 4.0
    while z < CROSS_END_Z + 4.0:
        z2 = z + step
        x1, x2 = crossover_x(z), crossover_x(z2)
        dx, dz = x2 - x1, z2 - z
        length = math.hypot(dx, dz)
        rot, euler = yaw_quat(dx, dz)
        nx, nz = dz / length, -dx / length        # unit normal in the ground plane
        for side in (-0.75, 0.75):
            kids.append(add_box(sc, root_t, "Rail",
                                ((x1 + x2) / 2 + nx * side, 0.48, (z + z2) / 2 + nz * side),
                                rot, euler, (0.12, 0.16, length + 0.04), MAT_STEEL))
        z = z2

    z = CROSS_START_Z + 0.6
    while z < CROSS_END_Z:
        x = crossover_x(z)
        if min(abs(x - TRAIN_X), abs(x - EAST_X)) > 1.6:
            dx = crossover_x(z + 0.1) - crossover_x(z - 0.1)
            rot, euler = yaw_quat(dx, 0.2)
            kids.append(add_box(sc, root_t, "Sleeper", (x, 0.33, z), rot, euler,
                                (2.5, 0.14, 0.26), MAT_SLEEPER))
        z += 1.2

    sc.add(go_block(root_g, "Crossover", [root_t]))
    sc.add(tr_block(root_t, root_g, (0, 0, 0), kids, 0))
    sc.roots.append(root_t)


def remove_prefab_instance(sc, name):
    inst = sc.prefab_instance_named(name)
    if inst is None:
        raise SystemExit("prefab instance missing from his scene: " + name)
    marker = "m_PrefabInstance: {fileID: %d}" % inst
    sc.blocks = [r for r in sc.blocks if r[1] != inst and marker not in r[3]]
    sc.roots = [r for r in sc.roots if r != inst]


def add_rail_pieces(sc, template_name, zs):
    """More of his straight double track, cloned from one of his rail instances."""
    src = sc.block(sc.prefab_instance_named(template_name))
    pattern = (r"(target: \{fileID: " + str(RAIL_TR) + ", guid: " + RAIL_GUID +
               r", type: 3\}\n\s+propertyPath: m_LocalPosition\.z\n\s+value: )\S+")
    for i, z in enumerate(zs):
        body = re.sub(pattern, r"\g<1>" + f(z), src[3])
        body = re.sub(r"(propertyPath: m_Name\n\s+value: ).*", r"\g<1>Straight rail (north %d)" % (i + 1),
                      body)
        a = sc.ids.new()
        sc.add(render(1001, a, False, body))
        sc.roots.append(a)


def add_north_terrain(sc):
    """A second terrain block, cloned from the pack's, pointing at the scene 3 ground."""
    guid = re.search(r"guid: (\w{32})", open(NORTH_TERRAIN + ".meta", encoding="utf-8").read()).group(1)
    src = open(PACK, encoding="utf-8").read()
    _, blocks = split_blocks(src)
    by_anchor = {a: (c, s, b) for c, a, s, b in blocks}
    remap = {old: sc.ids.new() for old in TERRAIN_ANCHORS}
    for old in TERRAIN_ANCHORS:
        cid, stripped, body = by_anchor[old]
        for o, n in remap.items():
            body = re.sub(r"\{fileID: %d\}" % o, "{fileID: %d}" % n, body)
        body = body.replace("guid: e908b8a036d743c40995d42c244c1204", "guid: " + guid)
        body = body.replace("m_Name: Terrain", "m_Name: Terrain (north)")
        body = re.sub(r"m_LocalPosition: \{[^}]*\}",
                      "m_LocalPosition: {x: %s, y: %s, z: %s}" % tuple(f(v) for v in NORTH_TERRAIN_POS),
                      body)
        sc.add(render(cid, remap[old], stripped, body))
    sc.roots.append(remap[1294392834])


def add_north_world(sc, drive_second_train):
    """Everything beyond the tunnel that scene 3 is played in: the ground, the rails running on,
    the crossover and its signal, and the dark red train waiting on our line.

    All three scenes carry it, so that the world through the tunnel is the same one whichever
    scene the player is in when they look, or drive, through it. Only scene 3 gives the red train
    its follower; elsewhere it just stands there, which is what it is doing until scene 3.

    Returns the TrainPathFollower's fileID, or None."""
    # His curve piece sits 1.83 above the line and across the west track exactly where the
    # crossover and the waiting train go, so it cannot stay.
    if sc.prefab_instance_named("Rail.L (1)") is not None:
        remove_prefab_instance(sc, "Rail.L (1)")
    add_rail_pieces(sc, "Straight rail (2)", EXTRA_RAIL_Z)

    # The crossover signal, on the same side of the line as his station signal.
    signal_pos = (APPROACH_SIGNAL_POS[0], APPROACH_SIGNAL_POS[1], SCENE3_SIGNAL_Z + 1.0)
    build_signal(sc, "Crossover Signal", signal_pos, red_on=True, yellow_on=False)
    hide_catenary_over_signal(sc, signal_pos[2])
    # The camera rides at gantry height, and on the stretch where the player brakes in scene 3
    # one of them fills the screen at exactly the wrong moment.
    hide_catenary_over_signal(sc, SCENE3_BRAKING_Z)
    build_crossover(sc)

    # The second train: his train again, turned to face the station and painted dark red.
    red_inst = sc.ids.new()
    tint_id = sc.ids.new()
    follower_id = sc.ids.new() if drive_second_train else None
    red_wheels_id = sc.ids.new() if drive_second_train else None
    added = [c for c in (follower_id, tint_id, red_wheels_id) if c is not None]
    sc.add(prefab_instance_block(
        red_inst, TRAIN_GUID, TRAIN_GO, TRAIN_TR, "Second Train",
        (TRAIN_X, TRAIN_Y, SECOND_TRAIN_START_Z), added=added,
        rot=(0, 1, 0, 0), euler=(0, 180, 0)))
    sc.roots.append(red_inst)
    red_go = sc.ids.new()
    sc.add(stripped_block(red_go, 1, "GameObject", TRAIN_GO, TRAIN_GUID, red_inst))
    sc.add(mono_block(tint_id, red_go, SCRIPTS["TrainTint"], """  materialName: Body
  tint: {r: 0.55, g: 0.08, b: 0.07, a: 1}"""))

    if drive_second_train:
        sc.add(mono_block(follower_id, red_go, SCRIPTS["TrainPathFollower"], """  westX: %s
  eastX: %s
  trackY: %s
  crossStartZ: %s
  crossEndZ: %s
  startZ: %s
  stopZ: %s
  maxSpeed: 20
  acceleration: 3
  deceleration: 3""" % (f(TRAIN_X), f(EAST_X), f(TRAIN_Y), f(CROSS_START_Z), f(CROSS_END_Z),
                        f(SECOND_TRAIN_START_Z), f(SECOND_TRAIN_STOP_Z))))
        sc.add(mono_block(red_wheels_id, red_go, SCRIPTS["TrainWheels"], WHEELS_FIELDS))

    add_north_terrain(sc)
    return follower_id


def add_north_world_to_scene1():
    """Adds the scene 3 world to the committed scene 1 file in place.

    Scene 1 is not regenerated by default, because it carries editor edits the generator does not
    know about (commit 0046853). So this patches the file on disk instead, and does nothing if the
    world is already there."""
    sc = Scene(SCENE1_OUT)
    if sc.find_go("Crossover") is not None:
        return False
    add_north_world(sc, drive_second_train=False)
    sc.write(SCENE1_OUT)
    return True


def build_scene3(his_guids):
    sc = Scene(SCENE1_SRC, pristine_scene1())

    # The station behind us looks the way it did when we left: signals red.
    paint_his_signal(sc, red_on=True, yellow_on=False, green_on=False)
    build_signal(sc, "Signal 1 (approach)", APPROACH_SIGNAL_POS, red_on=True, yellow_on=False)

    follower_id = add_north_world(sc, drive_second_train=True)

    # Our train, straight out of the tunnel. The director drives it.
    train_inst = sc.prefab_instance_named("train")
    train_go, train_tr = sc.ids.new(), sc.ids.new()
    wheels_id, audio_id = sc.ids.new(), sc.ids.new()
    patch_train_instance(sc, train_inst, SCENE3_PLAYER_START_Z, [wheels_id, audio_id], tag="Train")
    sc.add(stripped_block(train_go, 1, "GameObject", TRAIN_GO, TRAIN_GUID, train_inst))
    sc.add(stripped_block(train_tr, 4, "Transform", TRAIN_TR, TRAIN_GUID, train_inst))
    sc.add(mono_block(wheels_id, train_go, SCRIPTS["TrainWheels"], WHEELS_FIELDS))
    sc.add(mono_block(audio_id, train_go, SCRIPTS["TrainAudio"], AUDIO_FIELDS))

    # His Main Camera follows our train, exactly as in scene 1.
    cam_go = sc.find_go("Main Camera")
    follow = sc.ids.new()
    sc.add(mono_block(follow, cam_go, SCRIPTS["TrainFollowCamera"], """  target: {fileID: %d}
  localOffset: {x: %s, y: %s, z: %s}
  lookAtOffset: {x: %s, y: %s, z: %s}
  followSmoothing: 4
  snapOnStart: 1""" % (train_tr, f(FOLLOW_OFFSET[0]), f(FOLLOW_OFFSET[1]), f(FOLLOW_OFFSET[2]),
                       f(FOLLOW_LOOKAT[0]), f(FOLLOW_LOOKAT[1]), f(FOLLOW_LOOKAT[2]))))
    sc.add_component_to_go(cam_go, follow)
    cam_tr = sc.component_of_type(cam_go, 4)
    cpos = (TRAIN_X + FOLLOW_OFFSET[0], TRAIN_Y + FOLLOW_OFFSET[1], SCENE3_PLAYER_START_Z + FOLLOW_OFFSET[2])
    ctgt = (TRAIN_X + FOLLOW_LOOKAT[0], TRAIN_Y + FOLLOW_LOOKAT[1], SCENE3_PLAYER_START_Z + FOLLOW_LOOKAT[2])
    q = look_rotation(tuple(ctgt[i] - cpos[i] for i in range(3)))
    r = sc.block(cam_tr)
    r[3] = re.sub(r"m_LocalRotation: \{[^}]*\}",
                  "m_LocalRotation: {x: %s, y: %s, z: %s, w: %s}" % tuple(f(v) for v in q), r[3])
    r[3] = re.sub(r"m_LocalPosition: \{[^}]*\}",
                  "m_LocalPosition: {x: %s, y: %s, z: %s}" % tuple(f(v) for v in cpos), r[3])
    r[3] = re.sub(r"m_LocalEulerAnglesHint: \{[^}]*\}",
                  "m_LocalEulerAnglesHint: {x: %s, y: %s, z: %s}" % tuple(f(v) for v in euler_from_quat(q)),
                  r[3])

    apos, atgt = ARRIVAL_CAM
    q = look_rotation(tuple(atgt[i] - apos[i] for i in range(3)))
    at, ag, arrival_cam = sc.ids.new(), sc.ids.new(), sc.ids.new()
    sc.add(go_block(ag, "Cam_Arrival", [at, arrival_cam]))
    sc.add(tr_block(at, ag, apos, [], 0, rot=q, euler=euler_from_quat(q)))
    sc.add(camera_block(arrival_cam, ag, False))
    sc.roots.append(at)

    # The same framing on the second train, measured from its lead car rather than its pivot.
    lead = 50.54   # Front carType A, from the probe
    dt, dg, director = sc.ids.new(), sc.ids.new(), sc.ids.new()
    sc.add(go_block(dg, "Scene3Director", [dt, director]))
    sc.add(tr_block(dt, dg, (0, 0, 0), [], 0))
    sc.add(mono_block(director, dg, SCRIPTS["Scene3Director"], """  playerTrain: {fileID: %d}
  maxSpeed: 15
  acceleration: 1.2
  deceleration: 5
  noseOffset: %s
  signalZ: %s
  promptLead: 30
  secondTrain: {fileID: %d}
  cutToSecondTrainDelay: 1
  followCamera: {fileID: %d}
  secondTrainOffset: {x: 0, y: %s, z: %s}
  secondTrainLookAt: {x: 0, y: %s, z: %s}
  arrivalCamera: {fileID: %d}
  arrivalCutZ: %s
  firstSceneName: SampleScene
  endCardDelay: 1.5""" % (train_tr, f(TRAIN_NOSE), f(SCENE3_SIGNAL_Z), follower_id, follow,
                          f(FOLLOW_OFFSET[1]), f(FOLLOW_OFFSET[2] - lead),
                          f(FOLLOW_LOOKAT[1]), f(FOLLOW_LOOKAT[2] - lead),
                          arrival_cam, f(ARRIVAL_CUT_Z))))
    sc.roots.append(dt)

    add_station(sc)
    sc.write(SCENE3_OUT)

    meta = SCENE3_OUT + ".meta"
    if not os.path.exists(meta):
        open(meta, "w", encoding="utf-8", newline="\n").write(
            "fileFormatVersion: 2\nguid: %s\nDefaultImporter:\n  externalObjects: {}\n"
            "  userData: \n  assetBundleName: \n  assetBundleVariant: \n"
            % guid_for("Assets/Scenes/Scene3_Crossover.unity"))
    return sc


def add_scene3_to_build_settings():
    p = os.path.join(REPO, "ProjectSettings", "EditorBuildSettings.asset")
    s = open(p, encoding="utf-8").read()
    if "Scene3_Crossover.unity" in s:
        return False
    entry = ("  - enabled: 1\n    path: Assets/Scenes/Scene3_Crossover.unity\n    guid: %s\n"
             % guid_for("Assets/Scenes/Scene3_Crossover.unity"))
    s = s.replace("  m_configObjects:", entry + "  m_configObjects:", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    return True


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
    import sys

    g = his_script_guids()
    print("his script guids:", g)
    print("Train tag added:", add_train_tag())
    write_material("Crossover Steel", (0.42, 0.42, 0.44), 0.6, 0.45)
    write_material("Crossover Sleeper", (0.24, 0.17, 0.12), 0.0, 0.1)
    s2 = build_scene2(g)         # from his pristine scene, before scene 1 is overwritten
    print("scene 2 written:", SCENE2_OUT)
    s3 = build_scene3(g)
    print("scene 3 written:", SCENE3_OUT)
    print("scene 3 added to build settings:", add_scene3_to_build_settings())

    # Scene 1 carries hand edits made in the editor on 2026-09-13 (commit 0046853: Signal 1's
    # pole, housing and yellow lamp removed, train started further back) that were never folded
    # back into this generator, so rebuilding it would silently undo them. Opt in explicitly.
    if "--scene1" in sys.argv:
        s1 = build_scene1(g)
        print("scene 1 written:", SCENE1_OUT)
    else:
        print("scene 1 not rebuilt (pass --scene1 to rebuild it and lose the 0046853 edits);",
              "scene 3 world patched into it:", add_north_world_to_scene1())
