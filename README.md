# Train Sim

A three-chapter train simulation. You drive a train into a rural station, brake it at the platform in
front of a red signal, watch the passengers board, and pull away when the signal clears. Through the
tunnel you stop at a red signal to let a second train cross over and pass you, and follow it back
to the station.

Each chapter runs straight into the next — **you only ever open scene 1 and press Play.**

---

## Just want to play it? One file, no Unity

Grab the latest **Release** from the repo, unzip it, and double-click **`TrainSim.exe`**.

That is the whole thing. No Unity install, no editor version to match, no scenes to open, no Build
Settings. It boots straight into chapter 1, chapter 2 loads by itself when you stop the train, and
chapter 3 loads as you come out of the tunnel.

**Controls:** **Space** to brake, then **Space** again to pull away once the signal turns green, and
**Space** to stop at the signal past the tunnel. **R** retries a chapter you failed and replays from
the start at the end. **Alt+F4**, or **Esc** at the end, to quit.

The rest of this README is only for working on the project in Unity.

To produce that build yourself: open the project and run
**Tools → Train Sim → Build Windows Player**. It writes `Build/TrainSim/TrainSim.exe` with scene 1
as the startup scene. The build folder is deliberately **not committed** — a Unity player is a few
hundred MB and git would carry that weight in every clone forever, which is why it ships as a
Release attachment instead.

---

## Working on it in Unity

## What you need

| | |
|---|---|
| **Unity** | **6000.4.6f1** — the exact version this project targets |
| Git | to clone the repo |
| Disk | about 400 MB once Unity has built its Library |

### Installing the right Unity version

Unity Hub → **Installs** → **Install Editor** → **Archive** tab → *download archive* → find
**6000.4.6f1**. The free Personal licence is fine; sign in to Unity Hub once and it activates
itself.

> **Do not open this project in an older Unity.** In Unity 6.0 the packages
> `com.unity.xr.arcore`, `com.unity.xr.arfoundation`, `com.unity.modules.adaptiveperformance` and
> `com.unity.modules.vectorgraphics` do not exist, so the project fails to resolve and lands in
> Safe Mode. Opening it in an older editor also rewrites `ProjectSettings/ProjectVersion.txt`.

---

## Getting it

```bash
git clone https://github.com/biyonjose10/train_sim.git
cd train_sim
```

That is everything — models, animations, scenes and terrain are all committed. There is nothing
to download separately and no package to import from the Asset Store.

---

## Opening it

1. Open **Unity Hub** → **Projects** → **Add** → **Add project from disk**.
2. Pick the `train_sim` folder you just cloned.
3. Make sure the Editor Version column reads **6000.4.6f1**, then click the project to open it.

**The first open takes several minutes.** Unity is importing a 50 MB character, the terrain and the
asset packs, and building its Library from scratch. The progress bar will sit on
"Importing assets" for a while. This only happens once.

**Scene 1 opens by itself.** `Assets/Editor/OpenScene1OnLoad.cs` opens it the first time the
project loads in a session, because Unity otherwise starts on an empty "Untitled" scene and it
looks like nothing is there. It only steps in when no other scene is open, so it will not fight you
once you are working.

---

## Running it

**Press Play.** Scene 1 should already be open; if it is not, either:

- **Project** panel → `Assets` → `Scenes` → double-click **`SampleScene`**, or
- menu bar → **Tools → Train Sim → Open Scene 1**

Scene 2 loads by itself when the train stops, and scene 3 when it clears the tunnel. You do not open
either manually.

### Controls

| Key | Does |
|---|---|
| **Space** | Brake on the run in; then start and stop the train after the signal clears; then stop at the crossover signal |
| **R** | Retry scene 1 or 3 after passing a signal; replay from scene 1 at the end |
| **Esc** | Quit, on the end card |

### What should happen

1. The train runs in from the south on a camera sitting above and just behind its nose.
2. A distance and speed readout is on screen. **PRESS SPACE TO BRAKE** appears as you close in, and
   the readout turns **amber** at the point where braking any later would overshoot.
3. Press **space**. The train brakes and stops at the platform, nose two units short of the red
   signal. `STOPPED AT THE STATION` appears. If you sail past instead you get
   `YOU PASSED THE STATION` and can press **R**.
4. Scene 2 loads. The carriage doors slide open and eight passengers walk along the platform and
   board, across three camera shots.
5. At **9 seconds** the camera cuts back to the train with the red signal in frame. The doors
   close at 8.5 seconds, just before.
6. At **10 seconds** the signal turns **green** and **PRESS SPACE TO GO** appears.
7. Press **space** and the train pulls away toward the tunnel.
8. As the train comes out of the tunnel, scene 3 loads at the same speed. Ahead is a red signal, a
   crossover, and a **dark red train** waiting on your line facing you.
9. **PRESS SPACE TO STOP** appears with a distance readout, as in scene 1. Stop short of the signal
   and `STOPPED AT THE SIGNAL` appears. Run past it and you get `YOU PASSED THE SIGNAL`; the train
   brakes by itself well short of the points, and **R** retries scene 3.
10. The moment you are stopped the red train sets off. A second later the camera cuts to it: it
    crosses onto the other line, runs past you and back through the tunnel.
11. As it reaches the station the camera cuts to the north end of the far platform, the train stops
    alongside it, and **THE END** appears. **R** replays from scene 1, **Esc** quits.

The Console logs every beat (`[HUD]`, `[CAMERA]`, `[SIGNAL]`, `[DOOR]`, `[SCENE 3]`,
`[RED TRAIN]`), which is the quickest way
to confirm the sequence is running correctly.

---

## If something looks wrong

**Unity opens on an empty "Untitled" scene.**
The auto-open only runs once per session and skips if another scene is already open. Open
`Assets/Scenes/SampleScene` yourself, as above.

**You are looking at the station instead of the train, and Play starts mid-sequence.**
You have scene 2 open on its own. Scene 2 legitimately opens on a station camera, because that is
its first shot. Open scene 1 instead.

**Two of everything, and Play shows the wrong camera.**
You used **Open Both Scenes (inspect only)**. Each scene carries its own train, signals and
station, and scene 2's station camera renders over scene 1. That menu item is for comparing the two
side by side, never for playing. Open scene 1 on its own.

**Unity asks to enter Safe Mode, or the Console is full of errors about `TMPro` /
`UnityEngine.UI` / `UnityEngine.InputSystem`.**
Package resolution has not finished or has failed. Click **Ignore**, let it finish importing, then
restart the editor. If it persists you are almost certainly on the wrong Unity version.

**The scenes are not in the build.**
Run **Tools → Train Sim → Add Scenes To Build Settings**. Scene 1 cannot load scene 2, nor scene 2
load scene 3, unless all three are listed.

**Scene 3 has no ground, just sky under the rails.**
`Assets/Scenes/Scene3_NorthTerrain.asset` is missing. Run **Tools → Train Sim → Build Scene 3
Ground** to recreate it; it is deterministic, so you get the same ground and trees back.

---

## Editor menu

Everything lives under **Tools → Train Sim**:

| Item | Does |
|---|---|
| **Open Scene 1** | The playable chapter. This is the one you want |
| **Open Scene 2** | The boarding sequence on its own, for editing it in isolation |
| **Open Scene 3** | The crossover on its own. Playing it directly starts at full speed |
| **Open Both Scenes (inspect only)** | Loads scenes 1 and 2 together to compare. **Do not press Play** |
| **Add Scenes To Build Settings** | Registers all three scenes |
| **Build Scene 3 Ground** | Rebuilds the terrain north of the tunnel. Already applied |
| **Probe Layout** | Prints real mesh bounds and the platform extent |
| **Carve Tunnel Through Terrain** | Cuts the bore through the hill. Already applied |
| **Set Up Passenger Model** | Re-imports the Mixamo character and rebuilds its animator |
| **Build Windows Player** | Writes a standalone `Build/TrainSim/TrainSim.exe` |

---

## How the scenes are made

All three `.unity` files are **generated**, not hand-authored. `Tools/generate_scenes.py` builds
them from your teammate's original `SampleScene`, which is how the lighting, skybox, rails,
directional light and signal stay exactly his.

```bash
python Tools/generate_scenes.py            # rebuild scenes 2 and 3
python Tools/generate_scenes.py --scene1   # also rebuild scene 1 -- see the warning below
python Tools/validate_scene.py Assets/Scenes/Scene3_Crossover.unity   # structural check
```

> **Scene 1 is not rebuilt by default.** Commit `0046853` edited it in the editor (Signal 1's pole,
> housing and yellow lamp removed, the train started further back) and those edits were never
> folded into the generator, so `--scene1` would silently undo them.

Scene 3's layout (signal at z 187, crossover z 195–245, the red train's start and stop) is in the
`scene 3 layout` block of the generator. The crossover is an S-bend laid from primitive rails and
sleepers, because the pack's curve pieces are 90° bends; `TrainPathFollower.cs` drives each car of
the red train along the same formula, so if you change one, change both.

The generator always reads his scene from git (`origin/main`), never from the file on disk, so
re-running it never layers changes on top of a scene it already changed. Layout numbers live in the
`const` block at the top of that file — **change those and regenerate, rather than dragging objects
in the editor**, or the next regeneration will undo your work.

`SCENE2_README.md` has the technical detail: the coordinates, what was missing from scene 1
originally, and the known issues.

---

## Going back

Tagged restore points:

```bash
git tag -n1              # list them
git reset --hard working-v1   # back to a known good state
```

- **`working-v1`** — first version where both chapters played end to end
- **`working-v2`** — adds the HUD, sliding doors, glowing signals, rolling wheels and the passenger
  fixes

---

## Honest status

- The scenes were authored and verified in **6000.0.83f1** on a stripped-down copy, because the
  matching editor was not available at the time. They are **not yet verified in 6000.4.6f1**.
  They should import cleanly, but that is the first thing to check.
- **There is no audio.** `TrainAudio` and the director have clip slots wired up and null-guarded,
  so everything runs silently until clips are dropped in.
- All eight passengers are the same Mixamo character, varied by height, tint, speed and animation
  phase rather than being different people.
- The Mixamo FBX is 50 MB because it embeds full-resolution textures, which is over half the repo.
- The door panel sizes were estimated from the carriage bounds rather than matched to the model's
  window positions.
- **Scene 3** was played end to end in 6000.0.83f1 by a scripted run (scene 2 into scene 3, both
  the stop and the fail path), with screenshots checked at each beat. Nobody has played it by hand
  yet, and like the others it is not yet verified in 6000.4.6f1.
- Scene 3 drops the curved rail piece `Rail.L (1)` that his scene places just past the tunnel. It
  sits 1.83 above the line, right across where the crossover and the waiting train go.
- The pack terrain ends just past the tunnel, so scene 3 stands on a second terrain built from the
  pack's own ground layers, trees and grass. The red train is painted at runtime (`TrainTint`), so
  it looks grey in the editor until you press Play.
