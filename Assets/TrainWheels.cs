using UnityEngine;

/// <summary>
/// Rolls the train's wheels at a rate that matches how fast the train is actually travelling,
/// rather than spinning them at some arbitrary rate. The Train_Type A prefab carries 24 wheel
/// objects across its bogies; they are found by name at startup.
///
/// Reads whichever mover is on the train, so the same component works in both scenes.
/// </summary>
public class TrainWheels : MonoBehaviour
{
    [Header("Wheels")]
    public string wheelNamePrefix = "Wheel";
    public float wheelRadius = 0.45f;
    public Vector3 spinAxis = Vector3.right;

    [Header("Fallback")]
    // Used only if no mover component is present, so the wheels can still be tested by hand.
    public float manualSpeed = 0f;

    private Transform[] wheels;
    private TrainSpaceDrive drive;
    private Vector3 lastPosition;
    private float speed;

    void Start()
    {
        drive = GetComponent<TrainSpaceDrive>();
        lastPosition = transform.position;

        var found = new System.Collections.Generic.List<Transform>();

        foreach (Transform t in GetComponentsInChildren<Transform>(true))
        {
            if (t.name.StartsWith(wheelNamePrefix))
            {
                found.Add(t);
            }
        }

        wheels = found.ToArray();

        if (wheels.Length == 0)
        {
            Debug.LogWarning(
                "[WHEELS] No objects starting with '" + wheelNamePrefix +
                "' under " + gameObject.name + ", so nothing will turn."
            );
        }
        else
        {
            Debug.Log("[WHEELS] Rolling " + wheels.Length + " wheels.");
        }
    }

    void Update()
    {
        // Measure the speed off the transform. The train is moved by script in both scenes, and
        // this way the wheels cannot disagree with what is actually happening on screen.
        if (Time.deltaTime > 0f)
        {
            speed =
                Vector3.Distance(transform.position, lastPosition) /
                Time.deltaTime;
        }

        lastPosition = transform.position;

        if (drive != null && speed <= 0.001f)
        {
            speed = drive.CurrentSpeed;
        }

        if (speed <= 0.001f)
        {
            speed = manualSpeed;
        }

        if (wheels == null || speed <= 0.001f)
        {
            return;
        }

        // One revolution per 2*pi*r of travel.
        float degrees =
            (speed * Time.deltaTime) / (2f * Mathf.PI * Mathf.Max(wheelRadius, 0.01f)) * 360f;

        for (int i = 0; i < wheels.Length; i++)
        {
            if (wheels[i] != null)
            {
                wheels[i].Rotate(spinAxis, degrees, Space.Self);
            }
        }
    }
}
