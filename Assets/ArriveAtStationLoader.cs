using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// Drop this on the train in the first scene to hand over to scene 2 once the train has come
/// to rest at the platform. It deliberately watches the distance to the stop waypoint instead
/// of using a trigger, so it needs no tags and cannot be broken by an empty tag list.
///
/// Nothing in the first scene references this script yet. See SCENE2_README.md for the three
/// fields to fill in.
/// </summary>
public class ArriveAtStationLoader : MonoBehaviour
{
    [Header("Arrival Detection")]
    public Transform stationStopWaypoint;       // The same waypoint the train brakes towards
    public float arriveDistance = 0.5f;
    public float stationarySpeed = 0.05f;       // Treated as stopped below this, in units/second
    public float settleTime = 0.75f;            // How long it must stay stopped before loading

    [Header("Scene To Load")]
    public string nextSceneName = "Scene2_StationBoarding";
    public float loadDelay = 0.5f;

    private Vector3 lastPosition;
    private float settleTimer = 0f;
    private float loadTimer = -1f;
    private bool isLoading = false;

    void Start()
    {
        lastPosition = transform.position;
    }

    void Update()
    {
        if (isLoading)
        {
            return;
        }

        // ==========================================
        // COUNTDOWN ONCE ARRIVAL IS CONFIRMED
        // ==========================================

        if (loadTimer >= 0f)
        {
            loadTimer -= Time.deltaTime;

            if (loadTimer <= 0f)
            {
                LoadNextScene();
            }

            return;
        }

        if (stationStopWaypoint == null)
        {
            return;
        }

        // ==========================================
        // ARE WE STOPPED AT THE STATION?
        // ==========================================

        float speed =
            Time.deltaTime > 0f
                ? Vector3.Distance(transform.position, lastPosition) / Time.deltaTime
                : 0f;

        lastPosition = transform.position;

        float distanceToStation =
            Vector3.Distance(
                transform.position,
                stationStopWaypoint.position
            );

        bool atStation =
            distanceToStation <= arriveDistance &&
            speed <= stationarySpeed;

        if (!atStation)
        {
            settleTimer = 0f;
            return;
        }

        settleTimer += Time.deltaTime;

        if (settleTimer >= settleTime)
        {
            loadTimer = loadDelay;

            Debug.Log(
                "[SCENE 1] Train has settled at the station. Loading " +
                nextSceneName +
                "."
            );
        }
    }

    private void LoadNextScene()
    {
        if (string.IsNullOrEmpty(nextSceneName))
        {
            Debug.LogError(
                "[SCENE 1] No next scene name is set on ArriveAtStationLoader."
            );

            return;
        }

        if (Application.CanStreamedLevelBeLoaded(nextSceneName))
        {
            isLoading = true;

            SceneManager.LoadScene(nextSceneName);
        }
        else
        {
            Debug.LogError(
                "[SCENE 1] '" +
                nextSceneName +
                "' is not in Build Settings, so it cannot be loaded. " +
                "Add it under File > Build Profiles > Scene List."
            );

            enabled = false;
        }
    }
}
