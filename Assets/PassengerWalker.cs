using UnityEngine;

/// <summary>
/// Walks one Hitogatas figure along a short path and onto the train. The pack's figure ships
/// with a full humanoid skeleton but no animation clips and there is no animator controller
/// anywhere in the project, so the walk cycle is driven here by swinging the leg and arm bones
/// directly. If the bones cannot be found the figure still walks, it just does not swing.
/// </summary>
public class PassengerWalker : MonoBehaviour
{
    [Header("Path")]
    public Transform[] waypoints;
    public float moveSpeed = 1.4f;
    public float turnSpeed = 6f;
    public float startDelay = 0f;
    public float arriveDistance = 0.15f;

    [Header("Boarding")]
    public bool deactivateOnArrival = true;
    public float boardDelay = 0.2f;

    [Header("Walk Cycle")]
    public bool enableBoneWalk = true;
    public float stepFrequency = 2.2f;
    public float legSwingAngle = 26f;
    public float armSwingAngle = 16f;
    public Vector3 swingAxis = Vector3.right;

    [Header("Body Bob")]
    public float bobHeight = 0.035f;

    private int currentWaypoint = 0;
    private float waitTimer = 0f;
    private float arrivedTimer = -1f;
    private float walkPhase = 0f;

    private Vector3 bodyRestPosition;

    private Transform thighLeft;
    private Transform thighRight;
    private Transform armLeft;
    private Transform armRight;
    private Transform spine;

    private Quaternion thighLeftRest;
    private Quaternion thighRightRest;
    private Quaternion armLeftRest;
    private Quaternion armRightRest;

    void Start()
    {
        waitTimer = startDelay;

        // No controller exists, but an animator on the imported rig would still fight the
        // bone rotations written below.
        Animator animator = GetComponentInChildren<Animator>();

        if (animator != null)
        {
            animator.enabled = false;
        }

        CacheBones();
    }

    void Update()
    {
        if (waitTimer > 0f)
        {
            waitTimer -= Time.deltaTime;
            return;
        }

        // ==========================================
        // BOARDED
        // ==========================================

        if (arrivedTimer >= 0f)
        {
            arrivedTimer -= Time.deltaTime;

            if (arrivedTimer <= 0f &&
                deactivateOnArrival)
            {
                gameObject.SetActive(false);
            }

            return;
        }

        // ==========================================
        // WALK THE PATH
        // ==========================================

        if (waypoints == null ||
            currentWaypoint >= waypoints.Length)
        {
            Arrive();
            return;
        }

        Transform waypoint = waypoints[currentWaypoint];

        if (waypoint == null)
        {
            currentWaypoint++;
            return;
        }

        Vector3 target =
            new Vector3(
                waypoint.position.x,
                transform.position.y,
                waypoint.position.z
            );

        Vector3 toTarget =
            target - transform.position;

        if (toTarget.sqrMagnitude <= arriveDistance * arriveDistance)
        {
            currentWaypoint++;

            if (currentWaypoint >= waypoints.Length)
            {
                Arrive();
            }

            return;
        }

        transform.position =
            Vector3.MoveTowards(
                transform.position,
                target,
                moveSpeed * Time.deltaTime
            );

        Quaternion facing =
            Quaternion.LookRotation(toTarget.normalized, Vector3.up);

        transform.rotation =
            Quaternion.Slerp(
                transform.rotation,
                facing,
                1f - Mathf.Exp(-turnSpeed * Time.deltaTime)
            );

        walkPhase += stepFrequency * Time.deltaTime * Mathf.PI * 2f;
    }

    void LateUpdate()
    {
        if (!enableBoneWalk)
        {
            return;
        }

        ApplyWalkCycle();
    }

    // ==============================================
    // ARRIVAL
    // ==============================================

    private void Arrive()
    {
        if (arrivedTimer >= 0f)
        {
            return;
        }

        arrivedTimer = boardDelay;
    }

    // ==============================================
    // BONES
    // ==============================================

    private void CacheBones()
    {
        thighLeft = FindBone("thigh_stretch.l");
        thighRight = FindBone("thigh_stretch.r");
        armLeft = FindBone("arm_stretch.l");
        armRight = FindBone("arm_stretch.r");
        spine = FindBone("spine_01.x");

        if (thighLeft != null) thighLeftRest = thighLeft.localRotation;
        if (thighRight != null) thighRightRest = thighRight.localRotation;
        if (armLeft != null) armLeftRest = armLeft.localRotation;
        if (armRight != null) armRightRest = armRight.localRotation;
        if (spine != null) bodyRestPosition = spine.localPosition;

        if (thighLeft == null && thighRight == null)
        {
            Debug.LogWarning(
                "[PASSENGER] " +
                gameObject.name +
                " could not find its leg bones, so it will slide instead of walk."
            );
        }
    }

    private Transform FindBone(string boneName)
    {
        Transform[] all =
            GetComponentsInChildren<Transform>(true);

        for (int i = 0; i < all.Length; i++)
        {
            if (all[i].name == boneName)
            {
                return all[i];
            }
        }

        return null;
    }

    private void ApplyWalkCycle()
    {
        bool walking =
            arrivedTimer < 0f &&
            waitTimer <= 0f;

        float swing =
            walking ? Mathf.Sin(walkPhase) : 0f;

        SetBoneSwing(thighLeft, thighLeftRest, swing * legSwingAngle);
        SetBoneSwing(thighRight, thighRightRest, -swing * legSwingAngle);
        SetBoneSwing(armLeft, armLeftRest, -swing * armSwingAngle);
        SetBoneSwing(armRight, armRightRest, swing * armSwingAngle);

        if (spine != null)
        {
            float bob =
                walking
                    ? Mathf.Abs(Mathf.Sin(walkPhase)) * bobHeight
                    : 0f;

            spine.localPosition =
                bodyRestPosition + Vector3.up * bob;
        }
    }

    private void SetBoneSwing(Transform bone, Quaternion rest, float angle)
    {
        if (bone == null)
        {
            return;
        }

        bone.localRotation =
            rest * Quaternion.AngleAxis(angle, swingAxis);
    }
}
