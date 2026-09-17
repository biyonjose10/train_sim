using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// Hands scene 2 over to scene 3 as the train comes out of the far side of the tunnel.
///
/// Like ArriveAtStationLoader it watches the train's position rather than a trigger, so it needs
/// no tags or colliders. The speed the train was doing is carried across in TrainHandover, so
/// scene 3 opens with the train still rolling at the same pace instead of lurching.
/// </summary>
public class TunnelExitLoader : MonoBehaviour
{
    [Header("Hand Over")]
    public float handoverZ = 49.1f;             // train pivot z; its nose is then at about z 110
    public string nextSceneName = "Scene3_Crossover";

    private TrainSpaceDrive drive;
    private bool isLoading = false;

    void Start()
    {
        drive = GetComponent<TrainSpaceDrive>();
    }

    void Update()
    {
        if (isLoading || transform.position.z < handoverZ)
        {
            return;
        }

        if (!Application.CanStreamedLevelBeLoaded(nextSceneName))
        {
            Debug.LogError(
                "[SCENE 2] '" + nextSceneName + "' is not in Build Settings, so it cannot be " +
                "loaded. Run Tools > Train Sim > Add Scenes To Build Settings."
            );

            enabled = false;
            return;
        }

        isLoading = true;
        TrainHandover.Speed = drive != null ? drive.CurrentSpeed : -1f;

        Debug.Log(
            "[SCENE 2] Through the tunnel at " + TrainHandover.Speed.ToString("F1") +
            " units/s. Loading " + nextSceneName + "."
        );

        SceneManager.LoadScene(nextSceneName);
    }
}

/// <summary>
/// Carries the train's speed from one scene to the next. Negative means nothing was handed over,
/// which is the case when scene 3 is opened and played on its own in the editor.
/// </summary>
public static class TrainHandover
{
    public static float Speed = -1f;
}
