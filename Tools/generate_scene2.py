"""
Generates Assets/Scenes/Scene2_StationBoarding.unity without opening Unity.

The scene is the station environment scene verbatim, plus generated blocks for the track, the
stopped train, the signal, the cameras, the passengers and the director. Prefab instances are
written as scene roots, which is the exact shape every prefab instance in the source scene
already has -- the nested form is not used anywhere in that file, so it is not copied blind.

Deterministic: same input, same fileIDs and GUIDs, so re-running never breaks references.
"""

import hashlib
import math
import os
import re
import sys

REPO = r"C:\Users\biyon\projects\train_sim"

STATION = os.path.join(
    REPO, "Assets", "pixel horror abandoned rural  train station", "Scenes",
    "environment with station.unity")
SCENE1 = os.path.join(REPO, "Assets", "Scenes", "SampleScene.unity")
OUT = os.path.join(REPO, "Assets", "Scenes", "Scene2_StationBoarding.unity")

# ---------------------------------------------------------------- prefab identity

TRAIN_GUID = "7899c5f46e2286e4692bfa57b2f6c8e5"   # Prefabs/Train/Train_Type A.prefab
TRAIN_GO = 5680802176122678309
TRAIN_TR = 8443818322557161937

RAIL_GUID = "5134ed3777d4c484d8fe19fd21f2cc1e"    # Prefabs/Rail/Straight rail.prefab
RAIL_GO = 2171760524236046288
RAIL_TR = 1623647493005633391

PERSON_GUID = "ab147a2e39ef2ad4aa12cbc6597a626f"  # Models/Hitogatas.fbx
PERSON_GO = 919132149155446097
PERSON_TR = -8679921383154817045

PLAYER_GUID = "2f79b33e970aa464a978e550662078fc"
PLAYER_GO = 840457326483642086

MAT_RED = "a05474e98d8e14850be3e19a5f0a45b5"      # New Material.mat
MAT_YELLOW = "4edc65da92c7a4841b08cbd2e1ff65ea"   # New Material 3.mat
MAT_DARK = "9fa6d9495e43248479959c8c53531c6e"     # New Material 2.mat

MESH = "0000000000000000e000000000000000"
MESH_CUBE, MESH_CYLINDER, MESH_SPHERE = 10202, 10206, 10207


def guid_for(path):
    return hashlib.md5(("train_sim::" + path).encode()).hexdigest()


MAT_GREEN = guid_for("Assets/Materials/Signal Green.mat")

SCRIPTS = {
    n: guid_for("Assets/" + n + ".cs")
    for n in ("Scene2Director", "PassengerWalker", "TrainSpaceDrive",
              "TrainFollowCamera", "ArriveAtStationLoader")
}
SCRIPTS["Scene2Builder"] = guid_for("Assets/Editor/Scene2Builder.cs")

# ---------------------------------------------------------------- layout

TRACK_Y = 0.0
RAIL_Z = [-203.0, -101.5, 0.0, 101.5]

TRAIN_X, TRAIN_Y, TRAIN_STOP_Z = -2.4, 0.55, 6.0

DOOR_LINE_X = -3.9
DOOR_LOCAL_Z = [-21.0, -12.0, -3.0, 6.0]

PLATFORM_X, PLATFORM_TOP_Y = -6.9, 1.9

SIGNAL_POS = (-5.9773, 3.0711, 18.459)
SIGNAL_SCALE = 1.3712

SHOTS = [
    ("Cam_Station_A", (-9.8, 3.9, -14.0), (-4.6, 1.9, 2.0), True),
    ("Cam_Station_B", (-5.6, 2.5, -6.5), (-3.8, 1.9, 3.0), False),
    ("Cam_Station_C", (7.4, 3.4, -8.0), (-5.6, 2.8, 15.0), False),
]

FOLLOW_OFFSET = (5.5, 7.0, -26.0)
FOLLOW_LOOKAT = (-1.5, 2.0, 22.0)

PASSENGERS = [
    # spawn x, spawn z, start delay
    (-7.6, -19.0, 0.0), (-6.4, -15.0, 0.35), (-7.9, -10.0, 0.8), (-6.2, -6.0, 1.1),
    (-7.4, -1.0, 0.4), (-6.6, 3.0, 1.6), (-7.8, 8.0, 2.1), (-6.5, 11.0, 1.3),
]

# ---------------------------------------------------------------- fileID allocation

_used = set()
_next = [2300000000]


def new_id():
    while True:
        i = _next[0]
        _next[0] += 13
        if i not in _used:
            _used.add(i)
            return i


def f(v):
    """Unity writes floats without a trailing .0 when they are whole."""
    if v == int(v):
        return str(int(v))
    return repr(round(float(v), 7))


def look_rotation(fwd, up=(0.0, 1.0, 0.0)):
    fx, fy, fz = fwd
    n = math.sqrt(fx * fx + fy * fy + fz * fz)
    fx, fy, fz = fx / n, fy / n, fz / n
    ux, uy, uz = up
    rx, ry, rz = uy * fz - uz * fy, uz * fx - ux * fz, ux * fy - uy * fx
    n = math.sqrt(rx * rx + ry * ry + rz * rz)
    rx, ry, rz = rx / n, ry / n, rz / n
    ux, uy, uz = fy * rz - fz * ry, fz * rx - fx * rz, fx * ry - fy * rx
    m00, m01, m02 = rx, ux, fx
    m10, m11, m12 = ry, uy, fy
    m20, m21, m22 = rz, uz, fz
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
    sinp = 2 * (w * x - y * z)
    sinp = max(-1.0, min(1.0, sinp))
    pitch = math.asin(sinp)
    yaw = math.atan2(2 * (w * y + x * z), 1 - 2 * (x * x + y * y))
    roll = math.atan2(2 * (w * z + x * y), 1 - 2 * (x * x + z * z))
    d = 180.0 / math.pi
    return (pitch * d, yaw * d, roll * d)


# ---------------------------------------------------------------- block emitters

blocks = []


def go(name, transform_id, components, active=True, layer=0):
    i = new_id()
    comp = "\n".join("  - component: {fileID: %d}" % c for c in [transform_id] + components)
    blocks.append("""--- !u!1 &%d
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
%s
  m_Layer: %d
  m_Name: %s
  m_TagString: Untagged
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: %d""" % (i, comp, layer, name, 1 if active else 0))
    return i


def transform(tid, gid, pos, children, father, rot=(0, 0, 0, 1), scale=(1, 1, 1), euler=(0, 0, 0)):
    kids = "\n".join("  - {fileID: %d}" % c for c in children) if children else "  m_Children: []"
    kids_block = ("  m_Children:\n" + kids) if children else "  m_Children: []"
    blocks.append("""--- !u!4 &%d
Transform:
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
  m_LocalEulerAnglesHint: {x: %s, y: %s, z: %s}""" % (
        tid, gid,
        f(rot[0]), f(rot[1]), f(rot[2]), f(rot[3]),
        f(pos[0]), f(pos[1]), f(pos[2]),
        f(scale[0]), f(scale[1]), f(scale[2]),
        kids_block, father,
        f(euler[0]), f(euler[1]), f(euler[2])))


def camera(gid, enabled, fov=55.0, near=0.15, far=400.0):
    i = new_id()
    blocks.append("""--- !u!20 &%d
Camera:
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
  near clip plane: %s
  far clip plane: %s
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
  m_StereoSeparation: 0.022""" % (i, gid, 1 if enabled else 0, f(near), f(far), f(fov)))
    return i


def mesh_filter(gid, mesh_id):
    i = new_id()
    blocks.append("""--- !u!33 &%d
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Mesh: {fileID: %d, guid: %s, type: 0}""" % (i, gid, mesh_id, MESH))
    return i


def mesh_renderer(gid, mat_guid):
    i = new_id()
    blocks.append("""--- !u!23 &%d
MeshRenderer:
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
  m_AdditionalVertexStreams: {fileID: 0}""" % (i, gid, mat_guid))
    return i


def mono(gid, script, body):
    i = new_id()
    blocks.append("""--- !u!114 &%d
MonoBehaviour:
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
%s""" % (i, gid, SCRIPTS[script], body.rstrip()))
    return i


def audio_listener(gid):
    i = new_id()
    blocks.append("""--- !u!81 &%d
AudioListener:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: %d}
  m_Enabled: 1""" % (i, gid))
    return i


def prefab_instance(guid, go_target, tr_target, name, pos, added=None):
    """A prefab instance as a scene root, matching how the source scene writes every one."""
    i = new_id()
    mods = []

    def mod(target, path, value):
        mods.append("    - target: {fileID: %d, guid: %s, type: 3}\n"
                    "      propertyPath: %s\n"
                    "      value: %s\n"
                    "      objectReference: {fileID: 0}" % (target, guid, path, value))

    mod(go_target, "m_Name", name)
    for axis, v in zip("xyz", pos):
        mod(tr_target, "m_LocalPosition." + axis, f(v))
    for axis, v in zip("xyzw", (0, 0, 0, 1)):
        mod(tr_target, "m_LocalRotation." + axis, f(v))
    for axis in "xyz":
        mod(tr_target, "m_LocalEulerAnglesHint." + axis, "0")

    if added:
        added_block = "    m_AddedComponents:\n" + "\n".join(
            "    - targetCorrespondingSourceObject: {fileID: %d, guid: %s, type: 3}\n"
            "      insertIndex: -1\n"
            "      addedObject: {fileID: %d}" % (go_target, guid, a) for a in added)
    else:
        added_block = "    m_AddedComponents: []"

    blocks.append("""--- !u!1001 &%d
PrefabInstance:
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
  m_SourcePrefab: {fileID: 100100000, guid: %s, type: 3}""" % (
        i, "\n".join(mods), added_block, guid))
    return i


def stripped_go(instance, guid, source_go):
    i = new_id()
    blocks.append("""--- !u!1 &%d stripped
GameObject:
  m_CorrespondingSourceObject: {fileID: %d, guid: %s, type: 3}
  m_PrefabInstance: {fileID: %d}
  m_PrefabAsset: {fileID: 0}""" % (i, source_go, guid, instance))
    return i


def stripped_transform(instance, guid, source_tr):
    i = new_id()
    blocks.append("""--- !u!4 &%d stripped
Transform:
  m_CorrespondingSourceObject: {fileID: %d, guid: %s, type: 3}
  m_PrefabInstance: {fileID: %d}
  m_PrefabAsset: {fileID: 0}""" % (i, source_tr, guid, instance))
    return i


# ---------------------------------------------------------------- build the graph

def build():
    extra_roots = []

    # --- track -------------------------------------------------------------
    for z in RAIL_Z:
        extra_roots.append(
            prefab_instance(RAIL_GUID, RAIL_GO, RAIL_TR, "Straight rail",
                            (0.0, TRACK_Y, z)))

    # --- train -------------------------------------------------------------
    drive_id = new_id()
    train_inst = prefab_instance(TRAIN_GUID, TRAIN_GO, TRAIN_TR, "train",
                                 (TRAIN_X, TRAIN_Y, TRAIN_STOP_Z), added=[drive_id])
    extra_roots.append(train_inst)
    train_go = stripped_go(train_inst, TRAIN_GUID, TRAIN_GO)
    train_tr = stripped_transform(train_inst, TRAIN_GUID, TRAIN_TR)
    blocks.append("""--- !u!114 &%d
MonoBehaviour:
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
  maxSpeed: 15
  acceleration: 3
  deceleration: 5
  controlEnabled: 0
  startMoving: 0""" % (drive_id, train_go, SCRIPTS["TrainSpaceDrive"]))

    root_children = []

    # --- stop waypoint -----------------------------------------------------
    tid = new_id()
    gid = go("StationStopWaypoint", tid, [])
    transform(tid, gid, (TRAIN_X, TRAIN_Y, TRAIN_STOP_Z), [], 0)
    root_children.append(tid)

    # --- signal ------------------------------------------------------------
    sig_tr = new_id()
    lamp_gos = {}
    lamp_trs = []
    parts = [
        ("Cylinder", MESH_CYLINDER, MAT_DARK,
         (0.22247982, -2.44572, 0.07611084), (0.16854249, 1.6453941, 0.16854249), True),
        ("Cube", MESH_CUBE, MAT_DARK,
         (0.28247976, -0.08572006, 0.063), (0.57574, 1.6148355, 0.23222472), True),
        ("Sphere", MESH_SPHERE, MAT_RED,
         (0.32247972, 0.37427998, -0.027000427), (0.35476, 0.35476, 0.35476), True),
        ("Sphere (1)", MESH_SPHERE, MAT_YELLOW,
         (0.32247972, -0.12572002, -0.027000427), (0.35476, 0.35476, 0.35476), False),
        ("Sphere (2)", MESH_SPHERE, MAT_GREEN,
         (0.32247972, -0.6257199, -0.027000427), (0.35476, 0.35476, 0.35476), False),
    ]
    for name, mesh, mat, pos, scale, active in parts:
        t = new_id()
        g = go(name, t, [])
        mf = mesh_filter(g, mesh)
        mr = mesh_renderer(g, mat)
        # rewrite the GameObject block now that its components exist
        rewrite_components(g, [t, mf, mr], active)
        transform(t, g, pos, [], sig_tr, scale=scale)
        lamp_trs.append(t)
        lamp_gos[name] = g

    sig_go = go("signal", sig_tr, [])
    transform(sig_tr, sig_go, SIGNAL_POS, lamp_trs, 0,
              scale=(SIGNAL_SCALE, SIGNAL_SCALE, SIGNAL_SCALE))
    root_children.append(sig_tr)

    # --- cameras -----------------------------------------------------------
    cams_tr = new_id()
    cam_children = []
    cam_components = {}
    for name, pos, target, enabled in SHOTS:
        fwd = tuple(target[k] - pos[k] for k in range(3))
        q = look_rotation(fwd)
        t = new_id()
        g = go(name, t, [])
        c = camera(g, enabled)
        rewrite_components(g, [t, c], True)
        transform(t, g, pos, [], cams_tr, rot=q, euler=euler_from_quat(q))
        cam_children.append(t)
        cam_components[name] = c

    # train camera: placed where the follow script will hold it
    cam_pos = (TRAIN_X + FOLLOW_OFFSET[0], TRAIN_Y + FOLLOW_OFFSET[1],
               TRAIN_STOP_Z + FOLLOW_OFFSET[2])
    cam_target = (TRAIN_X + FOLLOW_LOOKAT[0], TRAIN_Y + FOLLOW_LOOKAT[1],
                  TRAIN_STOP_Z + FOLLOW_LOOKAT[2])
    q = look_rotation(tuple(cam_target[k] - cam_pos[k] for k in range(3)))
    t = new_id()
    g = go("Cam_Train", t, [])
    c = camera(g, False)
    follow = mono(g, "TrainFollowCamera", """  target: {fileID: %d}
  localOffset: {x: %s, y: %s, z: %s}
  lookAtOffset: {x: %s, y: %s, z: %s}
  followSmoothing: 4
  snapOnStart: 1""" % (train_tr,
                       f(FOLLOW_OFFSET[0]), f(FOLLOW_OFFSET[1]), f(FOLLOW_OFFSET[2]),
                       f(FOLLOW_LOOKAT[0]), f(FOLLOW_LOOKAT[1]), f(FOLLOW_LOOKAT[2])))
    rewrite_components(g, [t, c, follow], True)
    transform(t, g, cam_pos, [], cams_tr, rot=q, euler=euler_from_quat(q))
    cam_children.append(t)
    cam_components["Cam_Train"] = c

    cams_go = go("Cameras", cams_tr, [])
    transform(cams_tr, cams_go, (0, 0, 0), cam_children, 0)
    root_children.append(cams_tr)

    # --- passenger paths ---------------------------------------------------
    paths_tr = new_id()
    path_children = []
    door_points = []
    for i, (_, _, _) in enumerate(PASSENGERS):
        door_z = TRAIN_STOP_Z + DOOR_LOCAL_Z[i % len(DOOR_LOCAL_Z)]
        pt = new_id()
        pts = []
        for label, x in (("Queue", PLATFORM_X + 1.4), ("Door", DOOR_LINE_X)):
            t = new_id()
            g = go(label, t, [])
            transform(t, g, (x, PLATFORM_TOP_Y, door_z), [], pt)
            pts.append(t)
        pg = go("Path %d" % (i + 1), pt, [])
        transform(pt, pg, (0, 0, 0), pts, paths_tr)
        path_children.append(pt)
        door_points.append(pts)

    paths_go = go("Passenger Paths", paths_tr, [])
    transform(paths_tr, paths_go, (0, 0, 0), path_children, 0)
    root_children.append(paths_tr)

    # --- passengers --------------------------------------------------------
    for i, (sx, sz, delay) in enumerate(PASSENGERS):
        walker_id = new_id()
        inst = prefab_instance(PERSON_GUID, PERSON_GO, PERSON_TR,
                               "Passenger %d" % (i + 1),
                               (sx, PLATFORM_TOP_Y, sz), added=[walker_id])
        extra_roots.append(inst)
        pgo = stripped_go(inst, PERSON_GUID, PERSON_GO)
        blocks.append("""--- !u!114 &%d
MonoBehaviour:
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
  waypoints:
  - {fileID: %d}
  - {fileID: %d}
  moveSpeed: %s
  turnSpeed: 6
  startDelay: %s
  arriveDistance: 0.15
  deactivateOnArrival: 1
  boardDelay: 0.2
  enableBoneWalk: 1
  stepFrequency: 2.2
  legSwingAngle: 26
  armSwingAngle: 16
  swingAxis: {x: 1, y: 0, z: 0}
  bobHeight: 0.035""" % (walker_id, pgo, SCRIPTS["PassengerWalker"],
                         door_points[i][0], door_points[i][1],
                         f(1.25 + (i % 3) * 0.12), f(delay)))

    # --- director ----------------------------------------------------------
    d_tr = new_id()
    d_go = go("Scene2Director", d_tr, [])
    listener = audio_listener(d_go)
    director = mono(d_go, "Scene2Director", """  stationCameraA: {fileID: %d}
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
  promptFadeSpeed: 2""" % (
        cam_components["Cam_Station_A"], cam_components["Cam_Station_B"],
        cam_components["Cam_Station_C"], cam_components["Cam_Train"],
        lamp_gos["Sphere"], lamp_gos["Sphere (2)"], drive_id))
    rewrite_components(d_go, [d_tr, listener, director], True)
    transform(d_tr, d_go, (0, 0, 0), [], 0)
    root_children.append(d_tr)

    # --- setup root --------------------------------------------------------
    root_tr = new_id()
    root_go = go("SCENE 2 SETUP", root_tr, [])
    transform(root_tr, root_go, (0, 0, 0), root_children, 0)

    # reparent the direct children onto the root
    for child in root_children:
        set_father(child, root_tr)

    return [root_tr] + extra_roots


def blocks_last_instance():
    m = re.match(r"--- !u!1001 &(\d+)", blocks[-1])
    return int(m.group(1))


def rewrite_components(go_id, components, active):
    """GameObject blocks are emitted before their components exist, so patch them after."""
    for idx, b in enumerate(blocks):
        if b.startswith("--- !u!1 &%d\n" % go_id):
            comp = "\n".join("  - component: {fileID: %d}" % c for c in components)
            b = re.sub(r"  m_Component:\n(?:  - component: \{fileID: \d+\}\n)+",
                       "  m_Component:\n" + comp + "\n", b)
            b = re.sub(r"m_IsActive: \d", "m_IsActive: %d" % (1 if active else 0), b)
            blocks[idx] = b
            return
    raise SystemExit("could not patch GameObject %d" % go_id)


def set_father(transform_id, father):
    for idx, b in enumerate(blocks):
        if b.startswith("--- !u!4 &%d\n" % transform_id):
            blocks[idx] = re.sub(r"m_Father: \{fileID: \d+\}",
                                 "m_Father: {fileID: %d}" % father, b)
            return
    raise SystemExit("could not reparent transform %d" % transform_id)


# ---------------------------------------------------------------- assemble

def main():
    src = open(STATION, encoding="utf-8").read()

    for m in re.finditer(r"^--- !u!\d+ &(\d+)", src, re.M):
        _used.add(int(m.group(1)))

    new_roots = build()

    # Deactivate the free roam Player: this chapter is on rails, and its camera and audio
    # listener would otherwise fight the director.
    marker = ("    - target: {fileID: %d, guid: %s, type: 3}\n"
              "      propertyPath: m_Layer\n" % (PLAYER_GO, PLAYER_GUID))
    if marker not in src:
        raise SystemExit("could not find the Player prefab instance to deactivate")
    src = src.replace(marker,
                      "    - target: {fileID: %d, guid: %s, type: 3}\n"
                      "      propertyPath: m_IsActive\n"
                      "      value: 0\n"
                      "      objectReference: {fileID: 0}\n" % (PLAYER_GO, PLAYER_GUID)
                      + marker, 1)

    # Split off SceneRoots, append our blocks, then re-emit it with the new roots.
    idx = src.index("--- !u!1660057539 &")
    head, roots_block = src[:idx], src[idx:]

    extra = "\n".join("  - {fileID: %d}" % r for r in new_roots)
    roots_block = roots_block.rstrip("\n") + "\n" + extra + "\n"

    out = head + "\n".join(b.rstrip("\n") for b in blocks) + "\n" + roots_block
    open(OUT, "w", encoding="utf-8", newline="\n").write(out)

    print("wrote %s" % OUT)
    print("  blocks added : %d" % len(blocks))
    print("  new roots    : %d" % len(new_roots))
    return out


if __name__ == "__main__":
    main()
