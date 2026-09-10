using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Runs the scene 2 cutaway: the train is already stopped at the platform, the last signal is
/// red, and we have ten seconds of station footage before it turns green. At the ninth second
/// the camera cuts back to the train so the player is looking at the signal when it changes.
/// </summary>
public class Scene2Director : MonoBehaviour
{
    [Header("Station Shots")]
    public Camera stationCameraA;               // Wide, from under the west shelter
    public Camera stationCameraB;               // Close, at the carriage side
    public Camera stationCameraC;               // Across the tracks from the east platform
    public float shotBTime = 3.5f;
    public float shotCTime = 6.5f;

    [Header("Train Shot")]
    public Camera trainCamera;                  // Third person, follows the train
    public float cutToTrainTime = 9f;

    [Header("Last Signal Settings")]
    public GameObject lastSignalRedLight;       // Red sphere of the last signal
    public GameObject lastSignalGreenLight;     // Green sphere of the last signal
    public float greenLightDelay = 10f;

    [Header("Doors")]
    public TrainDoor[] trainDoors;
    public float doorsCloseTime = 8.5f;

    [Header("Audio")]
    public AudioClip stationAmbience;
    public AudioClip signalChange;
    public float ambienceVolume = 0.35f;

    [Header("Handover")]
    public TrainSpaceDrive trainDrive;
    public CanvasGroup pressSpacePrompt;
    public TMP_Text pressSpaceLabel;
    public float promptFadeSpeed = 2f;

    private float timer;

    private int currentShot = -1;

    private bool hasCutToTrain = false;
    private bool doorsClosed = false;
    private bool signalIsGreen = false;
    private bool promptDismissed = false;

    void Start()
    {
        timer = 0f;

        // Last signal starts RED
        if (lastSignalRedLight != null)
        {
            lastSignalRedLight.SetActive(true);
        }

        if (lastSignalGreenLight != null)
        {
            lastSignalGreenLight.SetActive(false);
        }

        // The player does not get the train until the signal clears.
        if (trainDrive != null)
        {
            trainDrive.controlEnabled = false;
        }

        EnsurePrompt();

        if (pressSpacePrompt != null)
        {
            pressSpacePrompt.alpha = 0f;
        }

        OpenDoors();
        StartAmbience();

        ShowShot(0);

        Debug.Log(
            "[SCENE 2] Train is at the platform. Signal turns GREEN in " +
            greenLightDelay +
            " seconds."
        );
    }

    void Update()
    {
        timer += Time.deltaTime;

        // ==========================================
        // STATION SHOTS
        // ==========================================

        if (!hasCutToTrain)
        {
            if (timer >= cutToTrainTime)
            {
                CutToTrain();
            }
            else if (timer >= shotCTime)
            {
                ShowShot(2);
            }
            else if (timer >= shotBTime)
            {
                ShowShot(1);
            }
            else
            {
                ShowShot(0);
            }
        }

        // ==========================================
        // DOORS
        // ==========================================

        // Shut before the signal clears, so the train is not pulling away with them open.
        if (!doorsClosed && timer >= doorsCloseTime)
        {
            doorsClosed = true;
            CloseDoors();
        }

        // ==========================================
        // LAST SIGNAL TURNS GREEN
        // ==========================================

        if (!signalIsGreen &&
            timer >= greenLightDelay)
        {
            TurnLastSignalGreen();
        }

        // ==========================================
        // PROMPT FADE
        // ==========================================

        UpdatePrompt();
    }

    // ==============================================
    // DOORS AND AMBIENCE
    // ==============================================

    private void OpenDoors()
    {
        if (trainDoors == null)
        {
            return;
        }

        foreach (TrainDoor door in trainDoors)
        {
            if (door != null)
            {
                door.Open();
            }
        }
    }

    private void CloseDoors()
    {
        if (trainDoors == null)
        {
            return;
        }

        foreach (TrainDoor door in trainDoors)
        {
            if (door != null)
            {
                door.Close();
            }
        }

        Debug.Log("[SCENE 2] Doors closing, boarding is over.");
    }

    private void StartAmbience()
    {
        if (stationAmbience == null)
        {
            return;
        }

        AudioSource source = gameObject.AddComponent<AudioSource>();
        source.clip = stationAmbience;
        source.loop = true;
        source.volume = ambienceVolume;
        source.spatialBlend = 0f;
        source.Play();
    }

    // ==============================================
    // CAMERA SWITCHING
    // ==============================================

    private void ShowShot(int index)
    {
        if (currentShot == index)
        {
            return;
        }

        currentShot = index;

        SetCameraEnabled(stationCameraA, index == 0);
        SetCameraEnabled(stationCameraB, index == 1);
        SetCameraEnabled(stationCameraC, index == 2);
        SetCameraEnabled(trainCamera, false);

        Debug.Log(
            "[CAMERA] Station shot " +
            (char)('A' + index) +
            " at " +
            timer.ToString("F2") +
            "s."
        );
    }

    private void CutToTrain()
    {
        hasCutToTrain = true;
        currentShot = 3;

        SetCameraEnabled(stationCameraA, false);
        SetCameraEnabled(stationCameraB, false);
        SetCameraEnabled(stationCameraC, false);
        SetCameraEnabled(trainCamera, true);

        Debug.Log(
            "[CAMERA] Cut to train view at " +
            timer.ToString("F2") +
            "s. The signal is still RED."
        );
    }

    private void SetCameraEnabled(Camera cam, bool state)
    {
        if (cam == null)
        {
            return;
        }

        cam.enabled = state;
    }

    // ==============================================
    // LAST SIGNAL TURNS GREEN
    // ==============================================

    private void TurnLastSignalGreen()
    {
        signalIsGreen = true;

        if (lastSignalRedLight != null)
        {
            lastSignalRedLight.SetActive(false);
        }

        if (lastSignalGreenLight != null)
        {
            lastSignalGreenLight.SetActive(true);
        }

        if (trainDrive != null)
        {
            trainDrive.controlEnabled = true;
        }

        if (pressSpaceLabel != null)
        {
            pressSpaceLabel.text = "PRESS SPACE TO GO";
        }

        if (signalChange != null && trainDrive != null)
        {
            TrainAudio audio = trainDrive.GetComponent<TrainAudio>();

            if (audio != null)
            {
                audio.PlayOneShot(signalChange, 0.9f);
            }
        }

        Debug.Log(
            "[SIGNAL] Last signal is now GREEN."
        );

        Debug.Log(
            "[SCENE 2] Control handed to the player. Press SPACE to start and stop the train."
        );
    }

    // ==============================================
    // PRESS SPACE PROMPT
    // ==============================================

    /// <summary>
    /// Builds the prompt in code when the scene does not already carry one. A canvas and a
    /// TextMeshPro label are a lot of serialized data for two words, and making them here keeps
    /// the scene file simple and the prompt impossible to lose.
    /// </summary>
    private void EnsurePrompt()
    {
        if (pressSpacePrompt != null)
        {
            return;
        }

        GameObject canvasObject = new GameObject("Scene2 Prompt Canvas");

        Canvas canvas = canvasObject.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;

        CanvasScaler scaler = canvasObject.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920f, 1080f);

        pressSpacePrompt = canvasObject.AddComponent<CanvasGroup>();
        pressSpacePrompt.alpha = 0f;
        pressSpacePrompt.interactable = false;
        pressSpacePrompt.blocksRaycasts = false;

        GameObject labelObject = new GameObject("PressSpaceLabel");
        labelObject.transform.SetParent(canvasObject.transform, false);

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

        pressSpaceLabel = label;
    }

    private void UpdatePrompt()
    {
        if (pressSpacePrompt == null)
        {
            return;
        }

        if (!promptDismissed &&
            signalIsGreen &&
            Keyboard.current != null &&
            Keyboard.current.spaceKey.wasPressedThisFrame)
        {
            promptDismissed = true;
        }

        float target =
            (signalIsGreen && !promptDismissed) ? 1f : 0f;

        pressSpacePrompt.alpha =
            Mathf.MoveTowards(
                pressSpacePrompt.alpha,
                target,
                promptFadeSpeed * Time.deltaTime
            );
    }
}
