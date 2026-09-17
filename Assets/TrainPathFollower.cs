using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Runs the second train in scene 3: south along the west track, over the crossover onto the
/// east track, back through the tunnel, and to a stop at the far platform.
///
/// The train is 122 units long and rigid, so moving the whole object along a curve would swing
/// its tail off the rails. Instead every car is placed on the route separately, at its own
/// distance along it, which is how a real train bends through points.
///
/// The crossover is an S-bend, x = mid + half * cos(pi * u), between crossStartZ (on the east
/// track) and crossEndZ (on the west track). Tools/generate_scenes.py lays its visible rails
/// with the same formula, so the cars follow the rails the player can see.
/// </summary>
public class TrainPathFollower : MonoBehaviour
{
    [Header("Tracks")]
    public float westX = -2.4f;
    public float eastX = 2.4f;
    public float trackY = 0.55f;

    [Header("Crossover")]
    public float crossStartZ = 195f;            // south end, on the east track
    public float crossEndZ = 245f;              // north end, on the west track

    [Header("Journey")]
    public float startZ = 310.9f;               // train pivot at the start, on the west track
    public float stopZ = -44.79f;               // train pivot at the stop, on the east track

    [Header("Speed")]
    public float maxSpeed = 20f;
    public float acceleration = 3f;
    public float deceleration = 3f;

    private readonly List<Vector3> points = new List<Vector3>();
    private readonly List<float> distances = new List<float>();

    private readonly List<Transform> cars = new List<Transform>();
    private readonly List<float> carOffsets = new List<float>();
    private readonly List<Quaternion> carLocalRotations = new List<Quaternion>();

    private float position;                     // distance of the pivot along the route
    private float endPosition;
    private float speed;
    private bool running;
    private bool arrived;

    public float CurrentSpeed { get { return speed; } }
    public bool Arrived { get { return arrived; } }
    public bool Running { get { return running; } }

    /// <summary>The car at the front in the direction of travel, for the camera to follow.</summary>
    public Transform LeadCar { get; private set; }

    void Awake()
    {
        BuildRoute();

        float bestOffset = float.MinValue;

        foreach (Transform child in transform)
        {
            if (!child.name.Contains("carType"))
            {
                continue;
            }

            cars.Add(child);
            carOffsets.Add(child.localPosition.z);
            carLocalRotations.Add(child.localRotation);

            if (child.localPosition.z > bestOffset)
            {
                bestOffset = child.localPosition.z;
                LeadCar = child;
            }
        }

        if (cars.Count == 0)
        {
            Debug.LogWarning("[RED TRAIN] No cars found under " + name + "; nothing will move.");
        }

        position = DistanceAtZ(startZ);
        endPosition = DistanceAtZ(stopZ);

        Place();
    }

    /// <summary>Sets the train off. Called by the scene 3 director once the player has stopped.</summary>
    public void Begin()
    {
        if (running || arrived)
        {
            return;
        }

        running = true;
        Debug.Log("[RED TRAIN] Pulling away towards the crossover.");
    }

    void Update()
    {
        if (!running)
        {
            return;
        }

        float remaining = endPosition - position;

        // Accelerate, but never faster than the speed that still lets it stop exactly on the mark.
        float brakingLimit = Mathf.Sqrt(2f * deceleration * Mathf.Max(remaining, 0f));

        speed = Mathf.Min(speed + acceleration * Time.deltaTime, maxSpeed, brakingLimit);
        position += speed * Time.deltaTime;

        if (remaining <= 0.02f || position >= endPosition)
        {
            position = endPosition;
            speed = 0f;
            running = false;
            arrived = true;

            Debug.Log("[RED TRAIN] Stopped at the far platform.");
        }

        Place();
    }

    // ==============================================
    // ROUTE
    // ==============================================

    private float XAtZ(float z)
    {
        if (z >= crossEndZ)
        {
            return westX;
        }

        if (z <= crossStartZ)
        {
            return eastX;
        }

        float u = (z - crossStartZ) / (crossEndZ - crossStartZ);
        float mid = (eastX + westX) * 0.5f;
        float half = (eastX - westX) * 0.5f;

        return mid + half * Mathf.Cos(Mathf.PI * u);
    }

    /// <summary>
    /// Samples the route from well behind the start to well past the stop, far enough that the
    /// rear car at the start and the lead car at the stop both still sit on it.
    /// </summary>
    private void BuildRoute()
    {
        const float step = 0.25f;
        const float margin = 80f;

        float top = startZ + margin;
        float bottom = stopZ - margin;

        float travelled = 0f;
        Vector3 previous = Vector3.zero;

        for (float z = top; z >= bottom; z -= step)
        {
            Vector3 p = new Vector3(XAtZ(z), trackY, z);

            if (points.Count > 0)
            {
                travelled += Vector3.Distance(previous, p);
            }

            points.Add(p);
            distances.Add(travelled);
            previous = p;
        }
    }

    private float DistanceAtZ(float z)
    {
        for (int i = 1; i < points.Count; i++)
        {
            if (points[i].z <= z)
            {
                return distances[i];
            }
        }

        return distances[distances.Count - 1];
    }

    private void Sample(float distance, out Vector3 point, out Vector3 tangent)
    {
        int last = distances.Count - 1;
        distance = Mathf.Clamp(distance, 0f, distances[last]);

        int lo = 0;
        int hi = last;

        while (hi - lo > 1)
        {
            int mid = (lo + hi) / 2;

            if (distances[mid] <= distance)
            {
                lo = mid;
            }
            else
            {
                hi = mid;
            }
        }

        float span = distances[hi] - distances[lo];
        float t = span > 0f ? (distance - distances[lo]) / span : 0f;

        point = Vector3.Lerp(points[lo], points[hi], t);
        tangent = (points[hi] - points[lo]).normalized;
    }

    private void Place()
    {
        Vector3 point;
        Vector3 tangent;

        // The root follows too, so anything measuring the train's own movement still sees it move.
        Sample(position, out point, out tangent);
        transform.SetPositionAndRotation(point, Quaternion.LookRotation(tangent));

        for (int i = 0; i < cars.Count; i++)
        {
            Sample(position + carOffsets[i], out point, out tangent);
            cars[i].SetPositionAndRotation(
                point,
                Quaternion.LookRotation(tangent) * carLocalRotations[i]
            );
        }
    }
}
