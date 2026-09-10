using UnityEngine;

/// <summary>
/// Makes eight copies of the same character stop looking like eight copies of the same character.
///
/// Everything is derived from a seed rather than from Random.Range at startup, so the platform
/// looks identical every run and a scene regenerated from the same numbers is reproducible.
///
/// The tint goes through a MaterialPropertyBlock, so no material assets are duplicated and the
/// shared Mixamo material stays untouched.
/// </summary>
public class PassengerVariety : MonoBehaviour
{
    [Header("Seed")]
    public int seed = 0;

    [Header("Height")]
    public float minScale = 0.94f;
    public float maxScale = 1.06f;

    [Header("Clothing Tint")]
    public bool tintClothing = true;
    public float tintStrength = 0.35f;

    [Header("Gait")]
    // Offsetting where each one starts in the walk cycle is what stops them stepping in unison.
    public bool offsetAnimator = true;

    void Start()
    {
        System.Random rng = new System.Random(seed * 7919 + 13);

        float Next()
        {
            return (float)rng.NextDouble();
        }

        float scale = Mathf.Lerp(minScale, maxScale, Next());
        transform.localScale = transform.localScale * scale;

        if (tintClothing)
        {
            Color tint =
                Color.HSVToRGB(
                    Next(),
                    Mathf.Lerp(0.15f, 0.5f, Next()),
                    Mathf.Lerp(0.55f, 0.9f, Next())
                );

            MaterialPropertyBlock block = new MaterialPropertyBlock();

            foreach (Renderer renderer in GetComponentsInChildren<Renderer>(true))
            {
                renderer.GetPropertyBlock(block);
                block.SetColor("_Color", Color.Lerp(Color.white, tint, tintStrength));
                renderer.SetPropertyBlock(block);
            }
        }

        if (offsetAnimator)
        {
            Animator animator = GetComponentInChildren<Animator>();

            if (animator != null && animator.runtimeAnimatorController != null)
            {
                animator.Play(0, 0, Next());
                // A little variation in stride rate as well, or they still look cloned.
                animator.speed = Mathf.Lerp(0.9f, 1.15f, Next());
            }
        }
    }
}
