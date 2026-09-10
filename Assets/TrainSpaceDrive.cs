using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Drives the train once the signal has cleared. Space toggles between going and stopping,
/// which keeps the control scheme in the same family as the spacebar brake used on the run
/// into the station.
/// </summary>
public class TrainSpaceDrive : MonoBehaviour
{
    [Header("Movement Settings")]
    public float maxSpeed = 15f;
    public float acceleration = 3f;
    public float deceleration = 5f;

    [Header("Control")]
    public bool controlEnabled = false;
    public bool startMoving = false;

    private float currentSpeed;
    private bool isMoving;

    void Start()
    {
        currentSpeed = 0f;
        isMoving = startMoving;

        Rigidbody rb = GetComponent<Rigidbody>();

        if (rb != null)
        {
            rb.isKinematic = true;
        }
    }

    void Update()
    {
        if (!controlEnabled)
        {
            return;
        }

        // ==========================================
        // SPACEBAR TOGGLE
        // ==========================================

        if (Keyboard.current != null &&
            Keyboard.current.spaceKey.wasPressedThisFrame)
        {
            isMoving = !isMoving;

            Debug.Log(
                isMoving
                    ? "[THROTTLE] Train is pulling away from the station."
                    : "[BRAKES APPLIED] Train is slowing to a stop."
            );
        }

        // ==========================================
        // SPEED
        // ==========================================

        float targetSpeed =
            isMoving ? maxSpeed : 0f;

        float rate =
            isMoving ? acceleration : deceleration;

        currentSpeed =
            Mathf.MoveTowards(
                currentSpeed,
                targetSpeed,
                rate * Time.deltaTime
            );

        if (currentSpeed <= 0f)
        {
            return;
        }

        // ==========================================
        // MOVEMENT
        // ==========================================

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
    }

    public float CurrentSpeed
    {
        get { return currentSpeed; }
    }

    public bool IsMoving
    {
        get { return isMoving; }
    }
}
