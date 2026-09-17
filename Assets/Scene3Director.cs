using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Runs scene 3: the crossover.
///
/// The player's train comes out of the tunnel still rolling. A second train is waiting on the
/// same track beyond a set of points, with a red signal protecting them. The player brakes
/// before the signal; the moment the train is at a stand the second train sets off, crosses over
/// onto the other line, runs past, and the camera goes with it back through the tunnel to the far
/// platform, where the game ends.
///
/// Passing the signal fails the scene, the same way overshooting the station fails scene 1.
/// </summary>
public class Scene3Director : MonoBehaviour
{
    [Header("Player Train")]
    public Transform playerTrain;
    public float maxSpeed = 15f;
    public float acceleration = 1.2f;
    public float deceleration = 5f;
    public float noseOffset = 60.91f;           // pivot to front of the train, from the probe

    [Header("Signal")]
    public float signalZ = 187f;                // the nose must stop short of this
    public float promptLead = 30f;              // start prompting this far before the brake point

    [Header("Second Train")]
    public TrainPathFollower secondTrain;
    public float cutToSecondTrainDelay = 1f;

    [Header("Camera")]
    public TrainFollowCamera followCamera;
    public Vector3 secondTrainOffset = new Vector3(0f, 7f, 1.46f);
    public Vector3 secondTrainLookAt = new Vector3(0f, 1.5f, 27.46f);

    [Header("Arrival")]
    // South of the station the pack terrain ends and there is only sky, which is where the chase
    // camera would be looking as the train stops. So it hands over to a camera by the platform.
    public Camera arrivalCamera;
    public float arrivalCutZ = 14f;             // lead car z where the train reaches the platform

    [Header("Ending")]
    public string firstSceneName = "SampleScene";
    public float endCardDelay = 1.5f;

    private enum Stage { Driving, Failed, Stopped, Following, Ended }

    private Stage stage = Stage.Driving;
    private float speed;
    private bool braking;
    private float stageTimer;
    private float arrivedTimer;
    private bool cutToArrival;

    private TMP_Text distanceLabel;
    private TMP_Text promptLabel;
    private TMP_Text verdictLabel;
    private TMP_Text hintLabel;

    void Start()
    {
        BuildHud();

        // Carry on at the speed scene 2 handed over, or at full speed when played on its own.
        speed = TrainHandover.Speed >= 0f ? TrainHandover.Speed : maxSpeed;
        TrainHandover.Speed = -1f;

        if (playerTrain == null || secondTrain == null || followCamera == null)
        {
            Debug.LogError("[SCENE 3] Player train, second train or camera is not assigned.");
            enabled = false;
            return;
        }

        Debug.Log(
            "[SCENE 3] Out of the tunnel at " + speed.ToString("F1") +
            " units/s. Stop before the signal at z " + signalZ + "."
        );
    }

    void Update()
    {
        stageTimer += Time.deltaTime;

        DrivePlayerTrain();

        switch (stage)
        {
            case Stage.Driving:
                UpdateDriving();
                break;

            case Stage.Failed:
                if (KeyPressed(Keyboard.current?.rKey))
                {
                    SceneManager.LoadScene(SceneManager.GetActiveScene().name);
                }
                break;

            case Stage.Stopped:
                if (stageTimer >= cutToSecondTrainDelay)
                {
                    CutToSecondTrain();
                }
                break;

            case Stage.Following:
                if (stageTimer >= 2.5f)
                {
                    verdictLabel.text = "";
                }

                if (!cutToArrival &&
                    arrivalCamera != null &&
                    secondTrain.LeadCar != null &&
                    secondTrain.LeadCar.position.z <= arrivalCutZ)
                {
                    CutToArrivalCamera();
                }

                if (secondTrain.Arrived)
                {
                    arrivedTimer += Time.deltaTime;

                    if (arrivedTimer >= endCardDelay)
                    {
                        ShowEndCard();
                    }
                }
                break;

            case Stage.Ended:
                if (KeyPressed(Keyboard.current?.rKey))
                {
                    SceneManager.LoadScene(firstSceneName);
                }
                else if (KeyPressed(Keyboard.current?.escapeKey))
                {
                    Quit();
                }
                break;
        }
    }

    // ==============================================
    // PLAYER TRAIN
    // ==============================================

    private void DrivePlayerTrain()
    {
        float rate = braking ? deceleration : acceleration;
        float target = braking ? 0f : maxSpeed;

        speed = Mathf.MoveTowards(speed, target, rate * Time.deltaTime);

        if (speed > 0f)
        {
            playerTrain.position += playerTrain.forward * speed * Time.deltaTime;
        }
    }

    private float NoseZ
    {
        get { return playerTrain.position.z + noseOffset; }
    }

    private void UpdateDriving()
    {
        float distance = signalZ - NoseZ;
        float stoppingDistance = (speed * speed) / (2f * Mathf.Max(deceleration, 0.01f));

        if (!braking && KeyPressed(Keyboard.current?.spaceKey))
        {
            braking = true;
            Debug.Log("[BRAKES APPLIED] Stopping for the signal.");
        }

        if (distance < 0f)
        {
            Fail();
            return;
        }

        if (braking && speed <= 0f)
        {
            StoppedAtSignal(distance);
            return;
        }

        distanceLabel.text =
            distance.ToString("F0") + " m to the signal     " +
            speed.ToString("F0") + " units/s";

        distanceLabel.color =
            (!braking && distance < stoppingDistance * 1.2f)
                ? new Color(1f, 0.75f, 0.2f)
                : Color.white;

        promptLabel.text =
            (!braking && distance < stoppingDistance + promptLead) ? "PRESS SPACE TO STOP" : "";
    }

    private void Fail()
    {
        stage = Stage.Failed;
        stageTimer = 0f;

        // Brake anyway, so the train does not carry on into the points.
        braking = true;

        distanceLabel.text = "";
        promptLabel.text = "";
        verdictLabel.text = "YOU PASSED THE SIGNAL";
        verdictLabel.color = new Color(1f, 0.5f, 0.45f);
        hintLabel.text = "Press R to try again";

        Debug.Log("[SCENE 3] Passed the red signal without stopping.");
    }

    private void StoppedAtSignal(float distance)
    {
        stage = Stage.Stopped;
        stageTimer = 0f;

        distanceLabel.text = "";
        promptLabel.text = "";
        verdictLabel.text = "STOPPED AT THE SIGNAL";
        verdictLabel.color = new Color(0.5f, 1f, 0.6f);

        secondTrain.Begin();

        Debug.Log(
            "[SCENE 3] Stopped " + distance.ToString("F1") +
            " m short of the signal. The second train is coming through."
        );
    }

    // ==============================================
    // SECOND TRAIN
    // ==============================================

    private void CutToSecondTrain()
    {
        stage = Stage.Following;
        stageTimer = 0f;

        followCamera.target = secondTrain.LeadCar != null
            ? secondTrain.LeadCar
            : secondTrain.transform;

        followCamera.localOffset = secondTrainOffset;
        followCamera.lookAtOffset = secondTrainLookAt;
        followCamera.SnapToTarget();

        Debug.Log("[CAMERA] Cut to the second train.");
    }

    private void CutToArrivalCamera()
    {
        cutToArrival = true;

        Camera chase = followCamera.GetComponent<Camera>();

        if (chase != null)
        {
            chase.enabled = false;
        }

        arrivalCamera.enabled = true;

        Debug.Log("[CAMERA] Cut to the platform as the second train arrives.");
    }

    private void ShowEndCard()
    {
        stage = Stage.Ended;
        stageTimer = 0f;

        verdictLabel.text = "THE END";
        verdictLabel.color = Color.white;
        verdictLabel.fontSize = 110f;
        hintLabel.text = "Press R to play again     Esc to quit";

        Debug.Log("[SCENE 3] The second train is at the platform. The end.");
    }

    private static void Quit()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }

    private static bool KeyPressed(UnityEngine.InputSystem.Controls.KeyControl key)
    {
        return key != null && key.wasPressedThisFrame;
    }

    // ==============================================
    // HUD
    // ==============================================

    /// <summary>Built in code, like the scene 1 HUD and the scene 2 prompt, and styled to match.</summary>
    private void BuildHud()
    {
        GameObject canvasObject = new GameObject("Scene3 HUD Canvas");

        Canvas canvas = canvasObject.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;

        CanvasScaler scaler = canvasObject.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920f, 1080f);

        distanceLabel = MakeLabel(canvasObject.transform, "Distance",
            new Vector2(0.5f, 1f), new Vector2(0f, -70f), 40f);

        promptLabel = MakeLabel(canvasObject.transform, "Prompt",
            new Vector2(0.5f, 0f), new Vector2(0f, 110f), 46f);

        verdictLabel = MakeLabel(canvasObject.transform, "Verdict",
            new Vector2(0.5f, 0.5f), new Vector2(0f, 40f), 60f);

        hintLabel = MakeLabel(canvasObject.transform, "Hint",
            new Vector2(0.5f, 0.5f), new Vector2(0f, -70f), 40f);
    }

    private TMP_Text MakeLabel(Transform parent, string name, Vector2 anchor,
                               Vector2 offset, float size)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);

        TextMeshProUGUI label = go.AddComponent<TextMeshProUGUI>();
        label.text = "";
        label.fontSize = size;
        label.alignment = TextAlignmentOptions.Center;
        label.color = Color.white;

        RectTransform rect = label.rectTransform;
        rect.anchorMin = anchor;
        rect.anchorMax = anchor;
        rect.pivot = new Vector2(0.5f, 0.5f);
        rect.anchoredPosition = offset;
        rect.sizeDelta = new Vector2(1200f, 160f);

        return label;
    }
}
