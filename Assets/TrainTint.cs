using UnityEngine;

/// <summary>
/// Repaints a train at startup by swapping the named materials on every renderer for tinted
/// copies. Used to make the second train in scene 3 dark red.
///
/// Done at runtime rather than as prefab material overrides because the Polyeler train spreads
/// its body material over dozens of renderers, and overriding each one in the scene file would
/// be a lot of fragile serialized data for one colour.
/// </summary>
public class TrainTint : MonoBehaviour
{
    public string materialName = "Body";
    public Color tint = new Color(0.55f, 0.08f, 0.07f);

    void Awake()
    {
        Material tinted = null;
        int swapped = 0;

        foreach (Renderer r in GetComponentsInChildren<Renderer>(true))
        {
            Material[] mats = r.sharedMaterials;
            bool changed = false;

            for (int i = 0; i < mats.Length; i++)
            {
                if (mats[i] == null || mats[i].name != materialName)
                {
                    continue;
                }

                if (tinted == null)
                {
                    tinted = new Material(mats[i]) { name = materialName + " (tinted)" };
                    tinted.color = tint;
                }

                mats[i] = tinted;
                changed = true;
                swapped++;
            }

            if (changed)
            {
                r.sharedMaterials = mats;
            }
        }

        if (swapped == 0)
        {
            Debug.LogWarning("[TINT] No '" + materialName + "' material found under " + name + ".");
        }
    }
}
