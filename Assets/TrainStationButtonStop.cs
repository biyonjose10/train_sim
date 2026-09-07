using UnityEngine;
using UnityEngine.InputSystem;

public class TrainStationButtonStop : MonoBehaviour
{
    [Header("Movement Settings")]
    public Transform stationStopWaypoint;       // Where the train stops at the station
    public Transform endOfTrackStopPoint;       // Final stopping point at the end of the track
    public float maxSpeed = 15f;

    [Header("Braking Settings")]
    public float maxDeceleration = 5f;

    [Header("Last Signal Settings")]
    public GameObject lastSignalRedLight;       // Red sphere of the last signal
    public GameObject lastSignalGreenLight;     // Green sphere of the last signal
    public float greenLightDelay = 10f;

    private float currentSpeed;

    private bool isStoppedAtStation = false;
    private bool hasPressedBrake = false;
    private bool missionFailed = false;
    private bool signalTimerStarted = false;

    private float distanceWhenBrakePressed = 0f;
    private float closestDistanceReached = float.MaxValue;

    void Start()
    {
        currentSpeed = maxSpeed;

        Rigidbody rb = GetComponent<Rigidbody>();

        if (rb != null)
        {
            rb.isKinematic = true;
        }

        // Last signal starts RED
        if (lastSignalRedLight != null)
        {
            lastSignalRedLight.SetActive(true);
        }

        if (lastSignalGreenLight != null)
        {
            lastSignalGreenLight.SetActive(false);
        }
    }

    void Update()
    {
        // ==========================================
        // FINAL END-OF-TRACK STOP
        // ==========================================

        if (endOfTrackStopPoint != null)
        {
            float distanceToEnd =
                Vector3.Distance(
                    transform.position,
                    endOfTrackStopPoint.position
                );

            // If the train reaches the end of the track,
            // stop it regardless of whether Space was pressed.
            if (distanceToEnd <= 0.05f)
            {
                transform.position =
                    endOfTrackStopPoint.position;

                currentSpeed = 0f;

                Debug.Log(
                    "[FINAL STOP] Train has reached the end of the track."
                );

                return;
            }
        }

        // ==========================================
        // STATION STOP
        // ==========================================

        if (isStoppedAtStation)
        {
            return;
        }

        if (stationStopWaypoint == null)
        {
            return;
        }

        float distanceToStation =
            Vector3.Distance(
                transform.position,
                stationStopWaypoint.position
            );

        // ==========================================
        // SPACEBAR BRAKE
        // ==========================================

        if (Keyboard.current != null &&
            Keyboard.current.spaceKey.wasPressedThisFrame &&
            !hasPressedBrake &&
            !missionFailed)
        {
            hasPressedBrake = true;

            distanceWhenBrakePressed =
                distanceToStation;

            Debug.Log(
                "[BRAKES APPLIED] Distance: " +
                distanceWhenBrakePressed.ToString("F2") +
                " units."
            );
        }

        // ==========================================
        // BRAKING TOWARD STATION
        // ==========================================

        if (hasPressedBrake)
        {
            if (distanceToStation <= 0.05f)
            {
                transform.position =
                    stationStopWaypoint.position;

                currentSpeed = 0f;

                isStoppedAtStation = true;

                Debug.Log(
                    "[MISSION SUCCESS] Train stopped at the station!"
                );

                // Start 10-second signal timer
                if (!signalTimerStarted)
                {
                    signalTimerStarted = true;

                    Invoke(
                        nameof(TurnLastSignalGreen),
                        greenLightDelay
                    );

                    Debug.Log(
                        "[SIGNAL] Last signal will turn GREEN in " +
                        greenLightDelay +
                        " seconds."
                    );
                }

                return;
            }

            // Calculate braking required to stop at station
            float requiredDeceleration =
                (currentSpeed * currentSpeed) /
                (2f * Mathf.Max(distanceToStation, 0.01f));

            float actualDeceleration =
                Mathf.Min(
                    requiredDeceleration,
                    maxDeceleration
                );

            currentSpeed -=
                actualDeceleration *
                Time.deltaTime;

            currentSpeed =
                Mathf.Max(currentSpeed, 0f);

            transform.position =
                Vector3.MoveTowards(
                    transform.position,
                    stationStopWaypoint.position,
                    currentSpeed *
                    Time.deltaTime
                );
        }

        // ==========================================
        // NORMAL MOVEMENT
        // ==========================================

        else
        {
            currentSpeed = maxSpeed;

            Vector3 movementTarget =
                transform.position +
                transform.forward * 500f;

            transform.position =
                Vector3.MoveTowards(
                    transform.position,
                    movementTarget,
                    currentSpeed *
                    Time.deltaTime
                );

            // ==========================================
            // CHECK IF TRAIN PASSED STATION
            // ==========================================

            if (!missionFailed)
            {
                if (distanceToStation <
                    closestDistanceReached)
                {
                    closestDistanceReached =
                        distanceToStation;
                }

                if (closestDistanceReached < 15f &&
                    distanceToStation >
                    closestDistanceReached + 2f)
                {
                    missionFailed = true;

                    Debug.LogError(
                        "[MISSION FAILED] " +
                        "You passed the station without braking!"
                    );
                }
            }
        }
    }

    // ==============================================
    // LAST SIGNAL TURNS GREEN
    // ==============================================

    private void TurnLastSignalGreen()
    {
        if (lastSignalRedLight != null)
        {
            lastSignalRedLight.SetActive(false);
        }

        if (lastSignalGreenLight != null)
        {
            lastSignalGreenLight.SetActive(true);
        }

        Debug.Log(
            "[SIGNAL] Last signal is now GREEN."
        );
    }
}