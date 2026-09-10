using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;

namespace TrainSim.SceneBuilding
{
    /// <summary>
    /// Builds scene 2 on top of a copy of the station environment scene. Everything this adds
    /// lives under a single root object, so running the build again simply replaces it. The
    /// numbers that decide where things sit are all in the block at the top: run
    /// Tools > Train Sim > Probe Scene 2 first and correct them against the real mesh bounds.
    /// </summary>
    public static class Scene2Builder
    {
        // ==========================================
        // PATHS
        // ==========================================

        const string StationScenePath =
            "Assets/pixel horror abandoned rural  train station/Scenes/environment with station.unity";

        const string Scene1Path =
            "Assets/Scenes/SampleScene.unity";

        const string Scene2Path =
            "Assets/Scenes/Scene2_StationBoarding.unity";

        const string TrainPrefabPath =
            "Assets/Polyeler/Simple Train Pack/Prefabs/Train/Train_Type A.prefab";

        const string RailPrefabPath =
            "Assets/Polyeler/Simple Train Pack/Prefabs/Rail/Straight rail.prefab";

        const string PassengerPrefabPath =
            "Assets/pixel horror abandoned rural  train station/Prefabs/Hitogatas.prefab";

        const string RedMaterialPath = "Assets/New Material.mat";      // 0.84, 0.09, 0.10
        const string YellowMaterialPath = "Assets/New Material 3.mat"; // 1.00, 0.98, 0.00
        const string DarkMaterialPath = "Assets/New Material 2.mat";   // black
        const string GreenMaterialPath = "Assets/Materials/Signal Green.mat";

        const string SetupRootName = "SCENE 2 SETUP";

        // ==========================================
        // LAYOUT  (verify these with the probe)
        // ==========================================

        // Track. The running line sits at x = 0 heading for the tunnel at z = +63.
        const float TrackY = 0f;
        static readonly float[] RailSegmentZ = { -203f, -101.5f, 0f, 101.5f };

        // Train. x and y are carried over from scene 1 so the two scenes agree.
        const float TrainX = -2.4f;
        const float TrainY = 0.55f;
        const float TrainStopZ = 6f;

        // Where the carriage side faces the platform, and the doors along it.
        const float DoorLineX = -3.9f;
        static readonly float[] DoorLocalZ = { -21f, -12f, -3f, 6f };

        // West platform: the left of the train as it faces the signal.
        const float PlatformX = -6.9f;
        const float PlatformTopY = 1.9f;

        // Signal, taken verbatim from scene 1.
        static readonly Vector3 SignalPosition = new Vector3(-5.9773f, 3.0711f, 18.459f);
        const float SignalScale = 1.3712f;

        // Cameras.
        static readonly Vector3 ShotAPosition = new Vector3(-9.8f, 3.9f, -14f);
        static readonly Vector3 ShotALookAt = new Vector3(-4.6f, 1.9f, 2f);

        static readonly Vector3 ShotBPosition = new Vector3(-5.6f, 2.5f, -6.5f);
        static readonly Vector3 ShotBLookAt = new Vector3(-3.8f, 1.9f, 3f);

        static readonly Vector3 ShotCPosition = new Vector3(7.4f, 3.4f, -8f);
        static readonly Vector3 ShotCLookAt = new Vector3(-5.6f, 2.8f, 15f);

        // ==========================================
        // MENU
        // ==========================================

        [MenuItem("Tools/Train Sim/Probe Scene 2", priority = 0)]
        public static void Probe()
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("===== SCENE 2 PROBE =====");

            ProbePrefab(sb, TrainPrefabPath);
            ProbePrefab(sb, RailPrefabPath);
            ProbePrefab(sb, PassengerPrefabPath);

            ProbePlatform(sb);

            Debug.Log(sb.ToString());
        }

        [MenuItem("Tools/Train Sim/Build Scene 2", priority = 1)]
        public static void Build()
        {
            if (!EnsureSceneCopy())
            {
                return;
            }

            Scene scene = EditorSceneManager.OpenScene(Scene2Path, OpenSceneMode.Single);

            ClearPreviousBuild(scene);
            DeactivateFreeRoamPlayer(scene);

            GameObject root = new GameObject(SetupRootName);

            GameObject track = BuildTrack(root.transform);
            GameObject train = BuildTrain(root.transform);
            Transform stopWaypoint = BuildStopWaypoint(root.transform);
            SignalParts signal = BuildSignal(root.transform);
            CameraSet cameras = BuildCameras(root.transform, train.transform);
            PromptParts prompt = BuildPrompt(root.transform);

            BuildPassengers(root.transform);

            WireDirector(root.transform, train, signal, cameras, prompt);

            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);

            AddScenesToBuildSettings();

            Debug.Log(
                "[BUILD] Scene 2 rebuilt. Track segments: " +
                track.transform.childCount +
                ", stop waypoint at " +
                stopWaypoint.position +
                "."
            );
        }

        [MenuItem("Tools/Train Sim/Add Scenes To Build Settings", priority = 2)]
        public static void AddScenesToBuildSettings()
        {
            var wanted = new List<EditorBuildSettingsScene>
            {
                new EditorBuildSettingsScene(Scene1Path, true),
                new EditorBuildSettingsScene(Scene2Path, true)
            };

            foreach (var existing in EditorBuildSettings.scenes)
            {
                if (existing.path != Scene1Path &&
                    existing.path != Scene2Path)
                {
                    wanted.Add(existing);
                }
            }

            EditorBuildSettings.scenes = wanted.ToArray();

            Debug.Log("[BUILD] Scene list now holds " + wanted.Count + " scenes.");
        }

        // ==========================================
        // SCENE COPY
        // ==========================================

        static bool EnsureSceneCopy()
        {
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(Scene2Path) != null)
            {
                return true;
            }

            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(StationScenePath) == null)
            {
                Debug.LogError("[BUILD] Cannot find the station scene at " + StationScenePath);
                return false;
            }

            if (!AssetDatabase.CopyAsset(StationScenePath, Scene2Path))
            {
                Debug.LogError("[BUILD] Failed to copy the station scene to " + Scene2Path);
                return false;
            }

            AssetDatabase.Refresh();

            Debug.Log("[BUILD] Copied the station layout to " + Scene2Path);

            return true;
        }

        static void ClearPreviousBuild(Scene scene)
        {
            foreach (GameObject go in scene.GetRootGameObjects())
            {
                if (go.name == SetupRootName)
                {
                    Object.DestroyImmediate(go);
                }
            }
        }

        static void DeactivateFreeRoamPlayer(Scene scene)
        {
            foreach (GameObject go in scene.GetRootGameObjects())
            {
                if (go.name == "Player")
                {
                    go.SetActive(false);

                    Debug.Log("[BUILD] Free roam Player switched off: scene 2 is on rails.");
                }
            }
        }

        // ==========================================
        // TRACK AND TRAIN
        // ==========================================

        static GameObject BuildTrack(Transform parent)
        {
            GameObject track = NewChild("Track", parent);

            GameObject railPrefab =
                AssetDatabase.LoadAssetAtPath<GameObject>(RailPrefabPath);

            if (railPrefab == null)
            {
                Debug.LogError("[BUILD] Missing rail prefab at " + RailPrefabPath);
                return track;
            }

            for (int i = 0; i < RailSegmentZ.Length; i++)
            {
                GameObject rail =
                    (GameObject)PrefabUtility.InstantiatePrefab(railPrefab, track.transform);

                rail.transform.position = new Vector3(0f, TrackY, RailSegmentZ[i]);
                rail.transform.rotation = Quaternion.identity;
            }

            return track;
        }

        static GameObject BuildTrain(Transform parent)
        {
            GameObject trainPrefab =
                AssetDatabase.LoadAssetAtPath<GameObject>(TrainPrefabPath);

            if (trainPrefab == null)
            {
                Debug.LogError("[BUILD] Missing train prefab at " + TrainPrefabPath);
                return NewChild("train", parent);
            }

            GameObject train =
                (GameObject)PrefabUtility.InstantiatePrefab(trainPrefab, parent);

            train.name = "train";
            train.transform.position = new Vector3(TrainX, TrainY, TrainStopZ);
            train.transform.rotation = Quaternion.identity;

            train.AddComponent<TrainSpaceDrive>();

            return train;
        }

        static Transform BuildStopWaypoint(Transform parent)
        {
            GameObject waypoint = NewChild("StationStopWaypoint", parent);

            waypoint.transform.position = new Vector3(TrainX, TrainY, TrainStopZ);

            return waypoint.transform;
        }

        // ==========================================
        // SIGNAL
        // ==========================================

        class SignalParts
        {
            public GameObject Root;
            public GameObject Red;
            public GameObject Yellow;
            public GameObject Green;
        }

        static SignalParts BuildSignal(Transform parent)
        {
            Material red = LoadMaterial(RedMaterialPath);
            Material yellow = LoadMaterial(YellowMaterialPath);
            Material dark = LoadMaterial(DarkMaterialPath);
            Material green = EnsureGreenMaterial();

            GameObject signal = NewChild("signal", parent);

            signal.transform.position = SignalPosition;
            signal.transform.localScale = Vector3.one * SignalScale;

            // Pole and backing plate, at the same local offsets the first scene uses.
            MakePrimitive(
                PrimitiveType.Cylinder, "Cylinder", signal.transform,
                new Vector3(0.22247982f, -2.44572f, 0.07611084f),
                new Vector3(0.16854249f, 1.6453941f, 0.16854249f),
                dark);

            MakePrimitive(
                PrimitiveType.Cube, "Cube", signal.transform,
                new Vector3(0.28247976f, -0.08572006f, 0.063f),
                new Vector3(0.57574f, 1.6148355f, 0.23222472f),
                dark);

            Vector3 lampScale = Vector3.one * 0.35476f;

            GameObject redLamp = MakePrimitive(
                PrimitiveType.Sphere, "Sphere", signal.transform,
                new Vector3(0.32247972f, 0.37427998f, -0.027000427f),
                lampScale, red);

            GameObject yellowLamp = MakePrimitive(
                PrimitiveType.Sphere, "Sphere (1)", signal.transform,
                new Vector3(0.32247972f, -0.12572002f, -0.027000427f),
                lampScale, yellow);

            GameObject greenLamp = MakePrimitive(
                PrimitiveType.Sphere, "Sphere (2)", signal.transform,
                new Vector3(0.32247972f, -0.6257199f, -0.027000427f),
                lampScale, green);

            // The train is held at this signal, so it opens red.
            redLamp.SetActive(true);
            yellowLamp.SetActive(false);
            greenLamp.SetActive(false);

            return new SignalParts
            {
                Root = signal,
                Red = redLamp,
                Yellow = yellowLamp,
                Green = greenLamp
            };
        }

        static Material EnsureGreenMaterial()
        {
            Material existing = AssetDatabase.LoadAssetAtPath<Material>(GreenMaterialPath);

            if (existing != null)
            {
                return existing;
            }

            if (!AssetDatabase.IsValidFolder("Assets/Materials"))
            {
                AssetDatabase.CreateFolder("Assets", "Materials");
            }

            // The project has red and yellow but no green, so make one in the same style:
            // Standard shader, plain colour, no emission.
            Material green = new Material(Shader.Find("Standard"));
            green.color = new Color(0.09f, 0.78f, 0.16f, 1f);

            AssetDatabase.CreateAsset(green, GreenMaterialPath);
            AssetDatabase.SaveAssets();

            Debug.Log("[BUILD] Created " + GreenMaterialPath);

            return green;
        }

        // ==========================================
        // CAMERAS
        // ==========================================

        class CameraSet
        {
            public Camera A;
            public Camera B;
            public Camera C;
            public Camera Train;
        }

        static CameraSet BuildCameras(Transform parent, Transform train)
        {
            GameObject group = NewChild("Cameras", parent);

            Camera a = MakeCamera("Cam_Station_A", group.transform, ShotAPosition, ShotALookAt, true);
            Camera b = MakeCamera("Cam_Station_B", group.transform, ShotBPosition, ShotBLookAt, false);
            Camera c = MakeCamera("Cam_Station_C", group.transform, ShotCPosition, ShotCLookAt, false);

            Camera trainCam = MakeCamera("Cam_Train", group.transform, Vector3.zero, Vector3.forward, false);

            TrainFollowCamera follow = trainCam.gameObject.AddComponent<TrainFollowCamera>();
            follow.target = train;

            // Frame the train from behind and slightly off the platform side, with the signal
            // ahead of it in shot.
            follow.localOffset = new Vector3(5.5f, 7f, -26f);
            follow.lookAtOffset = new Vector3(-1.5f, 2f, 22f);

            trainCam.transform.position = train.TransformPoint(follow.localOffset);
            trainCam.transform.LookAt(train.TransformPoint(follow.lookAtOffset));

            return new CameraSet { A = a, B = b, C = c, Train = trainCam };
        }

        static Camera MakeCamera(string name, Transform parent, Vector3 position, Vector3 lookAt, bool enabled)
        {
            GameObject go = NewChild(name, parent);

            go.transform.position = position;

            if ((lookAt - position).sqrMagnitude > 0.0001f)
            {
                go.transform.LookAt(lookAt);
            }

            Camera cam = go.AddComponent<Camera>();
            cam.enabled = enabled;
            cam.fieldOfView = 55f;
            cam.nearClipPlane = 0.15f;
            cam.farClipPlane = 400f;

            return cam;
        }

        // ==========================================
        // PASSENGERS
        // ==========================================

        static void BuildPassengers(Transform parent)
        {
            GameObject passengerPrefab =
                AssetDatabase.LoadAssetAtPath<GameObject>(PassengerPrefabPath);

            if (passengerPrefab == null)
            {
                Debug.LogError("[BUILD] Missing passenger prefab at " + PassengerPrefabPath);
                return;
            }

            GameObject people = NewChild("Passengers", parent);
            GameObject paths = NewChild("Passenger Paths", parent);

            // Spread along the west platform, each heading for one of the carriage doors.
            float[] spawnZ = { -19f, -15f, -10f, -6f, -1f, 3f, 8f, 11f };
            float[] spawnX = { -7.6f, -6.4f, -7.9f, -6.2f, -7.4f, -6.6f, -7.8f, -6.5f };
            float[] delay = { 0f, 0.35f, 0.8f, 1.1f, 0.4f, 1.6f, 2.1f, 1.3f };

            for (int i = 0; i < spawnZ.Length; i++)
            {
                float doorZ = TrainStopZ + DoorLocalZ[i % DoorLocalZ.Length];

                GameObject person =
                    (GameObject)PrefabUtility.InstantiatePrefab(passengerPrefab, people.transform);

                person.name = "Passenger " + (i + 1);
                person.transform.position = new Vector3(spawnX[i], PlatformTopY, spawnZ[i]);
                person.transform.rotation = Quaternion.identity;

                GameObject path = NewChild("Path " + (i + 1), paths.transform);

                GameObject queue = NewChild("Queue", path.transform);
                queue.transform.position = new Vector3(PlatformX + 1.4f, PlatformTopY, doorZ);

                GameObject door = NewChild("Door", path.transform);
                door.transform.position = new Vector3(DoorLineX, PlatformTopY, doorZ);

                PassengerWalker walker = person.AddComponent<PassengerWalker>();
                walker.waypoints = new[] { queue.transform, door.transform };
                walker.startDelay = delay[i];
                walker.moveSpeed = 1.25f + (i % 3) * 0.12f;
            }
        }

        // ==========================================
        // PROMPT
        // ==========================================

        class PromptParts
        {
            public CanvasGroup Group;
            public TMP_Text Label;
        }

        static PromptParts BuildPrompt(Transform parent)
        {
            GameObject ui = NewChild("UI", parent);

            GameObject canvasObject = NewChild("Canvas", ui.transform);

            Canvas canvas = canvasObject.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;

            CanvasScaler scaler = canvasObject.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);

            CanvasGroup group = canvasObject.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            group.interactable = false;
            group.blocksRaycasts = false;

            GameObject labelObject = NewChild("PressSpaceLabel", canvasObject.transform);

            TextMeshProUGUI label = labelObject.AddComponent<TextMeshProUGUI>();
            label.text = "PRESS SPACE";
            label.fontSize = 42f;
            label.alignment = TextAlignmentOptions.Center;
            label.color = Color.white;

            RectTransform rect = label.rectTransform;
            rect.anchorMin = new Vector2(0.5f, 0f);
            rect.anchorMax = new Vector2(0.5f, 0f);
            rect.pivot = new Vector2(0.5f, 0f);
            rect.anchoredPosition = new Vector2(0f, 90f);
            rect.sizeDelta = new Vector2(600f, 80f);

            return new PromptParts { Group = group, Label = label };
        }

        // ==========================================
        // DIRECTOR
        // ==========================================

        static void WireDirector(
            Transform parent,
            GameObject train,
            SignalParts signal,
            CameraSet cameras,
            PromptParts prompt)
        {
            GameObject go = NewChild("Scene2Director", parent);

            // Nothing in the scene plays audio, but a scene with no listener logs a warning
            // on every play, so one lives here rather than on a camera that gets disabled.
            go.AddComponent<AudioListener>();

            Scene2Director director = go.AddComponent<Scene2Director>();

            director.stationCameraA = cameras.A;
            director.stationCameraB = cameras.B;
            director.stationCameraC = cameras.C;
            director.trainCamera = cameras.Train;

            director.shotBTime = 3.5f;
            director.shotCTime = 6.5f;
            director.cutToTrainTime = 9f;
            director.greenLightDelay = 10f;

            director.lastSignalRedLight = signal.Red;
            director.lastSignalGreenLight = signal.Green;

            director.trainDrive = train.GetComponent<TrainSpaceDrive>();
            director.pressSpacePrompt = prompt.Group;
            director.pressSpaceLabel = prompt.Label;
        }

        // ==========================================
        // HELPERS
        // ==========================================

        static GameObject NewChild(string name, Transform parent)
        {
            GameObject go = new GameObject(name);
            go.transform.SetParent(parent, false);
            return go;
        }

        static GameObject MakePrimitive(
            PrimitiveType type,
            string name,
            Transform parent,
            Vector3 localPosition,
            Vector3 localScale,
            Material material)
        {
            GameObject go = GameObject.CreatePrimitive(type);

            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPosition;
            go.transform.localScale = localScale;

            // The signal sits at the platform edge; colliders on it would only get in the
            // way of the passengers.
            Collider collider = go.GetComponent<Collider>();

            if (collider != null)
            {
                Object.DestroyImmediate(collider);
            }

            if (material != null)
            {
                go.GetComponent<Renderer>().sharedMaterial = material;
            }

            return go;
        }

        static Material LoadMaterial(string path)
        {
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);

            if (material == null)
            {
                Debug.LogWarning("[BUILD] Missing material at " + path);
            }

            return material;
        }

        // ==========================================
        // PROBE
        // ==========================================

        static void ProbePrefab(System.Text.StringBuilder sb, string path)
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);

            if (prefab == null)
            {
                sb.AppendLine("MISSING: " + path);
                return;
            }

            GameObject instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            instance.transform.position = Vector3.zero;
            instance.transform.rotation = Quaternion.identity;

            Bounds bounds = new Bounds(Vector3.zero, Vector3.zero);
            bool first = true;

            foreach (Renderer renderer in instance.GetComponentsInChildren<Renderer>())
            {
                if (first)
                {
                    bounds = renderer.bounds;
                    first = false;
                }
                else
                {
                    bounds.Encapsulate(renderer.bounds);
                }
            }

            sb.AppendLine(System.IO.Path.GetFileNameWithoutExtension(path));
            sb.AppendLine("   size   " + bounds.size);
            sb.AppendLine("   centre " + bounds.center);
            sb.AppendLine("   min    " + bounds.min);
            sb.AppendLine("   max    " + bounds.max);

            Object.DestroyImmediate(instance);
        }

        static void ProbePlatform(System.Text.StringBuilder sb)
        {
            Scene scene = EditorSceneManager.OpenScene(StationScenePath, OpenSceneMode.Additive);

            float bestTop = float.MinValue;
            string bestName = "none";

            foreach (GameObject root in scene.GetRootGameObjects())
            {
                if (!root.name.StartsWith("cement platform"))
                {
                    continue;
                }

                foreach (Renderer renderer in root.GetComponentsInChildren<Renderer>())
                {
                    if (renderer.bounds.max.y > bestTop)
                    {
                        bestTop = renderer.bounds.max.y;
                        bestName = root.name;
                    }
                }

                sb.AppendLine(
                    "platform " + root.name +
                    "  pos " + root.transform.position);
            }

            sb.AppendLine("highest platform surface y = " + bestTop + "  (" + bestName + ")");

            EditorSceneManager.CloseScene(scene, true);
        }
    }
}
