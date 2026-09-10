using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// The heads up display for the run in.
///
/// Without this the first scene tells the player nothing: there is no instruction to brake, no way
/// to judge the stopping distance, and the success and failure messages only reach the console,
/// which nobody sees in a build.
///
/// It works entirely off the train's transform and its own measured speed, so his
/// TrainStationButtonStop does not need to expose anything and stays untouched.
/// </summary>
public class Scene1Hud : MonoBehaviour
{
    [Header("What to watch")]
    public Transform train;
    public Transform stationStopWaypoint;

    [Header("Braking")]
    // Matches his script: 15 units/s shedding 5 units/s/s needs about 22.5 units.
    public float maxSpeed = 15f;
    public float maxDeceleration = 5f;
    public float promptLead = 30f;          // start nagging this far before the brake point
    public float arriveDistance = 0.6f;

    [Header("Restart")]
    public string restartKeyName = "R";

    private TMP_Text distanceLabel;
    private TMP_Text promptLabel;
    private TMP_Text verdictLabel;
    private CanvasGroup group;

    private Vector3 lastPosition;
    private float speed;
    private float closest = float.MaxValue;
    private bool braking;
    private bool finished;

    void Start()
    {
        BuildHud();

        if (train != null)
        {
            lastPosition = train.position;
        }

        if (train == null || stationStopWaypoint == null)
        {
            Debug.LogWarning("[HUD] Train or stop waypoint not assigned; the HUD will stay blank.");
        }
    }

    void Update()
    {
        if (train == null || stationStopWaypoint == null)
        {
            return;
        }

        // ==========================================
        // SPEED AND DISTANCE
        // ==========================================

        if (Time.deltaTime > 0f)
        {
            speed = Vector3.Distance(train.position, lastPosition) / Time.deltaTime;
        }

        lastPosition = train.position;

        float distance =
            Vector3.Distance(train.position, stationStopWaypoint.position);

        float stoppingDistance =
            (speed * speed) / (2f * Mathf.Max(maxDeceleration, 0.01f));

        if (Keyboard.current != null &&
            Keyboard.current.spaceKey.wasPressedThisFrame)
        {
            braking = true;
        }

        // ==========================================
        // OUTCOME
        // ==========================================

        if (!finished)
        {
            closest = Mathf.Min(closest, distance);

            if (distance <= arriveDistance && speed < 0.05f)
            {
                Finish(true);
            }
            else if (closest < 15f && distance > closest + 3f)
            {
                Finish(false);
            }
        }

        // ==========================================
        // LABELS
        // ==========================================

        if (!finished)
        {
            distanceLabel.text =
                distance.ToString("F0") + " m to the stop     " +
                speed.ToString("F0") + " units/s";

            bool needToBrake =
                !braking && distance < stoppingDistance + promptLead;

            promptLabel.text = needToBrake ? "PRESS SPACE TO BRAKE" : "";

            // Turn the readout amber once braking any later would overshoot.
            distanceLabel.color =
                (!braking && distance < stoppingDistance * 1.2f)
                    ? new Color(1f, 0.75f, 0.2f)
                    : Color.white;
        }

        if (finished &&
            Keyboard.current != null &&
            Keyboard.current.rKey.wasPressedThisFrame)
        {
            SceneManager.LoadScene(SceneManager.GetActiveScene().name);
        }
    }

    private void Finish(bool success)
    {
        finished = true;

        promptLabel.text = "";
        distanceLabel.text = "";

        verdictLabel.text =
            success
                ? "STOPPED AT THE STATION"
                : "YOU PASSED THE STATION\n\nPress " + restartKeyName + " to try again";

        verdictLabel.color =
            success ? new Color(0.5f, 1f, 0.6f) : new Color(1f, 0.5f, 0.45f);

        Debug.Log(success
            ? "[HUD] Stopped at the station."
            : "[HUD] Passed the station without braking.");
    }

    // ==============================================
    // HUD CONSTRUCTION
    // ==============================================

    /// <summary>
    /// Built in code for the same reason the scene 2 prompt is: a canvas plus three TextMeshPro
    /// labels is a lot of serialized data to carry in a scene file for a few lines of text.
    /// </summary>
    private void BuildHud()
    {
        GameObject canvasObject = new GameObject("Scene1 HUD Canvas");

        Canvas canvas = canvasObject.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;

        CanvasScaler scaler = canvasObject.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920f, 1080f);

        group = canvasObject.AddComponent<CanvasGroup>();
        group.interactable = false;
        group.blocksRaycasts = false;

        distanceLabel = MakeLabel(canvasObject.transform, "Distance",
            new Vector2(0.5f, 1f), new Vector2(0f, -70f), 40f, TextAlignmentOptions.Center);

        promptLabel = MakeLabel(canvasObject.transform, "Prompt",
            new Vector2(0.5f, 0f), new Vector2(0f, 110f), 46f, TextAlignmentOptions.Center);

        verdictLabel = MakeLabel(canvasObject.transform, "Verdict",
            new Vector2(0.5f, 0.5f), new Vector2(0f, 0f), 60f, TextAlignmentOptions.Center);
    }

    private TMP_Text MakeLabel(Transform parent, string name, Vector2 anchor,
                               Vector2 offset, float size, TextAlignmentOptions align)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);

        TextMeshProUGUI label = go.AddComponent<TextMeshProUGUI>();
        label.text = "";
        label.fontSize = size;
        label.alignment = align;
        label.color = Color.white;

        RectTransform rect = label.rectTransform;
        rect.anchorMin = anchor;
        rect.anchorMax = anchor;
        rect.pivot = new Vector2(0.5f, 0.5f);
        rect.anchoredPosition = offset;
        rect.sizeDelta = new Vector2(900f, 140f);

        return label;
    }
}
