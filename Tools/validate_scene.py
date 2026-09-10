"""Structural check on a hand-generated Unity scene, since we cannot open the editor."""

import re
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()

problems = []

# ---------------------------------------------------------------- parse blocks
blocks = {}          # anchor -> (classid, body, stripped)
order = []
for m in re.finditer(r"^--- !u!(\d+) &(-?\d+)( stripped)?\n(.*?)(?=^--- |\Z)",
                     src, re.M | re.S):
    cid, anchor, stripped, body = int(m.group(1)), int(m.group(2)), bool(m.group(3)), m.group(4)
    if anchor in blocks:
        problems.append("duplicate anchor %d" % anchor)
    blocks[anchor] = (cid, body, stripped)
    order.append(anchor)

print("blocks parsed: %d" % len(blocks))

# ---------------------------------------------------------------- reference check
# Only local references matter: anything carrying a guid points outside this file.
local_ref = re.compile(r"\{fileID: (-?\d+)\}")
for anchor, (cid, body, stripped) in blocks.items():
    for line in body.splitlines():
        if "guid:" in line:
            continue
        for m in local_ref.finditer(line):
            tgt = int(m.group(1))
            if tgt == 0:
                continue
            if tgt not in blocks:
                problems.append("anchor %d (!u!%d) references missing fileID %d  [%s]"
                                % (anchor, cid, tgt, line.strip()))

# ---------------------------------------------------------------- transform graph
transforms = {a: b for a, (c, b, s) in blocks.items() if c == 4 and not s}
stripped_tr = {a for a, (c, b, s) in blocks.items() if c == 4 and s}
gameobjects = {a: b for a, (c, b, s) in blocks.items() if c == 1 and not s}

children_of = {}
father_of = {}
for a, body in transforms.items():
    kids = []
    mkids = re.search(r"  m_Children:\n((?:  - \{fileID: -?\d+\}\n)*)", body)
    if mkids:
        kids = [int(x) for x in re.findall(r"\{fileID: (-?\d+)\}", mkids.group(1))]
    children_of[a] = kids
    mf = re.search(r"m_Father: \{fileID: (-?\d+)\}", body)
    father_of[a] = int(mf.group(1)) if mf else None

for a, kids in children_of.items():
    for k in kids:
        if k in stripped_tr:
            continue
        if k not in transforms:
            problems.append("transform %d lists child %d which is not a transform" % (a, k))
        elif father_of.get(k) != a:
            problems.append("transform %d lists child %d, but that child's father is %s"
                            % (a, k, father_of.get(k)))

for a, fa in father_of.items():
    if fa and fa != 0:
        if fa not in transforms:
            problems.append("transform %d has father %d which is not a transform" % (a, fa))
        elif a not in children_of.get(fa, []):
            problems.append("transform %d says father %d, but that father does not list it"
                            % (a, fa))

# ---------------------------------------------------------------- GameObject <-> components
for a, body in gameobjects.items():
    comps = [int(x) for x in re.findall(r"  - component: \{fileID: (-?\d+)\}", body)]
    if not comps:
        problems.append("GameObject %d has no components" % a)
    for c in comps:
        if c not in blocks:
            problems.append("GameObject %d lists missing component %d" % (a, c))
            continue
        cbody = blocks[c][1]
        mg = re.search(r"m_GameObject: \{fileID: (-?\d+)\}", cbody)
        if not mg or int(mg.group(1)) != a:
            problems.append("GameObject %d lists component %d whose m_GameObject is %s"
                            % (a, c, mg.group(1) if mg else "absent"))
    if not any(blocks[c][0] == 4 for c in comps if c in blocks):
        problems.append("GameObject %d has no Transform" % a)

# ---------------------------------------------------------------- SceneRoots
roots_block = [a for a, (c, b, s) in blocks.items() if c == 1660057539]
if len(roots_block) != 1:
    problems.append("expected exactly one SceneRoots, found %d" % len(roots_block))
else:
    body = blocks[roots_block[0]][1]
    listed = [int(x) for x in re.findall(r"  - \{fileID: (-?\d+)\}", body)]
    if len(listed) != len(set(listed)):
        problems.append("SceneRoots has duplicate entries")
    actual_roots = {a for a, fa in father_of.items() if fa == 0}
    prefab_roots = {a for a, (c, b, s) in blocks.items() if c == 1001
                    and re.search(r"m_TransformParent: \{fileID: 0\}", b)}
    listed_set = set(listed)
    missing = (actual_roots | prefab_roots) - listed_set
    extra = listed_set - (actual_roots | prefab_roots)
    if missing:
        problems.append("SceneRoots is missing %d root(s): %s"
                        % (len(missing), sorted(missing)[:8]))
    if extra:
        problems.append("SceneRoots lists %d non-root(s): %s"
                        % (len(extra), sorted(extra)[:8]))
    print("scene roots listed: %d" % len(listed))

# ---------------------------------------------------------------- prefab instances
for a, (c, body, s) in blocks.items():
    if c != 1001:
        continue
    if "m_SourcePrefab: {fileID: 100100000" not in body:
        problems.append("PrefabInstance %d has no source prefab" % a)
    for m in re.finditer(r"addedObject: \{fileID: (-?\d+)\}", body):
        if int(m.group(1)) not in blocks:
            problems.append("PrefabInstance %d adds missing object %s" % (a, m.group(1)))

# stripped objects must name a live instance
for a, (c, body, s) in blocks.items():
    if not s:
        continue
    m = re.search(r"m_PrefabInstance: \{fileID: (-?\d+)\}", body)
    if not m or int(m.group(1)) not in blocks:
        problems.append("stripped object %d points at a missing PrefabInstance" % a)

# ---------------------------------------------------------------- indentation sanity
for i, line in enumerate(src.splitlines(), 1):
    if line.startswith("\t"):
        problems.append("line %d uses a tab" % i)

print()
if problems:
    print("FAILED: %d problem(s)" % len(problems))
    for p in problems[:40]:
        print("  -", p)
    sys.exit(1)
print("OK: structure is consistent")
