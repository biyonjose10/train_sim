using UnityEngine;

/// <summary>
/// Third person camera that trails the train, matching the outside view the run into the
/// station is shot from. The offset is in the train's local space, so it stays behind and
/// above the train whichever way the train is facing.
/// </summary>
public class TrainFollowCamera : MonoBehaviour
{
    [Header("Target")]
    public Transform target;

    [Header("Framing")]
    public Vector3 localOffset = new Vector3(6f, 7f, -26f);
    public Vector3 lookAtOffset = new Vector3(0f, 2f, 24f);

    [Header("Smoothing")]
    public float followSmoothing = 4f;
    public bool snapOnStart = true;

    void Start()
    {
        if (snapOnStart)
        {
            SnapToTarget();
        }
    }

    void LateUpdate()
    {
        if (target == null)
        {
            return;
        }

        Vector3 desiredPosition =
            target.TransformPoint(localOffset);

        transform.position =
            Vector3.Lerp(
                transform.position,
                desiredPosition,
                1f - Mathf.Exp(-followSmoothing * Time.deltaTime)
            );

        transform.LookAt(
            target.TransformPoint(lookAtOffset)
        );
    }

    public void SnapToTarget()
    {
        if (target == null)
        {
            return;
        }

        transform.position =
            target.TransformPoint(localOffset);

        transform.LookAt(
            target.TransformPoint(lookAtOffset)
        );
    }
}
