using UnityEngine;

/// <summary>
/// A pair of sliding panels on the side of a carriage.
///
/// The Polyeler train has no door geometry at all, so these are built from primitives and sat
/// flush against the carriage skin. They give the passengers something to walk into, which is
/// what makes the boarding read as boarding rather than as figures blinking out of existence.
/// </summary>
public class TrainDoor : MonoBehaviour
{
    [Header("Panels")]
    public Transform leftPanel;
    public Transform rightPanel;

    [Header("Slide")]
    public float openOffset = 0.62f;        // how far each panel slides, along local Z
    public float slideSpeed = 1.6f;

    [Header("State")]
    public bool startOpen = false;

    private Vector3 leftClosed;
    private Vector3 rightClosed;
    private float openAmount;
    private bool wantOpen;

    void Awake()
    {
        if (leftPanel != null)
        {
            leftClosed = leftPanel.localPosition;
        }

        if (rightPanel != null)
        {
            rightClosed = rightPanel.localPosition;
        }

        wantOpen = startOpen;
        openAmount = startOpen ? 1f : 0f;

        Apply();
    }

    void Update()
    {
        float target = wantOpen ? 1f : 0f;

        if (Mathf.Approximately(openAmount, target))
        {
            return;
        }

        openAmount =
            Mathf.MoveTowards(
                openAmount,
                target,
                slideSpeed * Time.deltaTime
            );

        Apply();
    }

    private void Apply()
    {
        // Smoothstep so the panels ease rather than snapping at each end.
        float t = openAmount * openAmount * (3f - 2f * openAmount);

        if (leftPanel != null)
        {
            leftPanel.localPosition =
                leftClosed + Vector3.forward * (openOffset * t);
        }

        if (rightPanel != null)
        {
            rightPanel.localPosition =
                rightClosed - Vector3.forward * (openOffset * t);
        }
    }

    public void Open()
    {
        if (!wantOpen)
        {
            Debug.Log("[DOOR] " + gameObject.name + " opening.");
        }

        wantOpen = true;
    }

    public void Close()
    {
        if (wantOpen)
        {
            Debug.Log("[DOOR] " + gameObject.name + " closing.");
        }

        wantOpen = false;
    }

    /// <summary>Wide enough for a passenger to step through.</summary>
    public bool IsOpenEnough
    {
        get { return openAmount > 0.6f; }
    }
}
