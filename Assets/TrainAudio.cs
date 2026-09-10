using UnityEngine;

/// <summary>
/// Engine noise for the train, driven by how fast it is actually moving.
///
/// Every clip is optional. With none assigned the component does nothing at all rather than
/// throwing, so the scenes still run before any audio has been imported.
/// </summary>
public class TrainAudio : MonoBehaviour
{
    [Header("Clips")]
    public AudioClip rumbleLoop;
    public AudioClip brakeSqueal;

    [Header("Rumble")]
    public float maxSpeed = 15f;
    public float minPitch = 0.55f;
    public float maxPitch = 1.25f;
    public float maxVolume = 0.7f;
    public float fadeSpeed = 2f;

    [Header("Brake")]
    public float squealVolume = 0.8f;
    // Only squeal when actually shedding real speed, not when crawling to a halt.
    public float squealSpeedThreshold = 4f;

    private AudioSource rumble;
    private AudioSource oneShots;
    private Vector3 lastPosition;
    private float speed;
    private float lastSpeed;
    private bool squealed;

    void Start()
    {
        lastPosition = transform.position;

        oneShots = gameObject.AddComponent<AudioSource>();
        oneShots.playOnAwake = false;
        oneShots.spatialBlend = 0f;

        if (rumbleLoop != null)
        {
            rumble = gameObject.AddComponent<AudioSource>();
            rumble.clip = rumbleLoop;
            rumble.loop = true;
            rumble.volume = 0f;
            rumble.spatialBlend = 0f;
            rumble.Play();
        }
    }

    void Update()
    {
        if (Time.deltaTime > 0f)
        {
            speed = Vector3.Distance(transform.position, lastPosition) / Time.deltaTime;
        }

        lastPosition = transform.position;

        // ==========================================
        // RUMBLE
        // ==========================================

        if (rumble != null)
        {
            float t = Mathf.Clamp01(speed / Mathf.Max(maxSpeed, 0.01f));

            rumble.pitch = Mathf.Lerp(minPitch, maxPitch, t);

            rumble.volume =
                Mathf.MoveTowards(
                    rumble.volume,
                    t * maxVolume,
                    fadeSpeed * Time.deltaTime
                );
        }

        // ==========================================
        // BRAKE SQUEAL
        // ==========================================

        if (brakeSqueal != null && !squealed &&
            speed > 0.2f && speed < lastSpeed - 0.02f &&
            lastSpeed > squealSpeedThreshold)
        {
            squealed = true;
            oneShots.PlayOneShot(brakeSqueal, squealVolume);
        }

        // Rearm once the train is moving freely again.
        if (speed > lastSpeed + 0.02f)
        {
            squealed = false;
        }

        lastSpeed = speed;
    }

    /// <summary>Play a one shot from elsewhere, for example the signal changing.</summary>
    public void PlayOneShot(AudioClip clip, float volume)
    {
        if (clip != null && oneShots != null)
        {
            oneShots.PlayOneShot(clip, volume);
        }
    }
}
