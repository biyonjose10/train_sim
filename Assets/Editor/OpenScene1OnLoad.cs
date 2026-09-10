using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TrainSim.SceneBuilding
{
    /// <summary>
    /// Opens scene 1 the first time the project is loaded in a session.
    ///
    /// Unity otherwise starts on an empty "Untitled" scene, which has caught everyone who has
    /// opened this project so far: it looks like nothing is there. Scene 1 is the one to be in,
    /// because it loads scene 2 itself.
    ///
    /// Only fires when the open scene is untitled, so it never fights you once you are working.
    /// </summary>
    [InitializeOnLoad]
    public static class OpenScene1OnLoad
    {
        const string Scene1Path = "Assets/Scenes/SampleScene.unity";
        const string DoneKey = "TrainSim.OpenedScene1";

        static OpenScene1OnLoad()
        {
            EditorApplication.delayCall += TryOpen;
        }

        static void TryOpen()
        {
            if (SessionState.GetBool(DoneKey, false))
            {
                return;
            }

            SessionState.SetBool(DoneKey, true);

            // Only step in when nothing real is open, and never mid play.
            if (EditorApplication.isPlayingOrWillChangePlaymode ||
                !string.IsNullOrEmpty(EditorSceneManager.GetActiveScene().path))
            {
                return;
            }

            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(Scene1Path) == null)
            {
                return;
            }

            EditorSceneManager.OpenScene(Scene1Path, OpenSceneMode.Single);

            Debug.Log(
                "[TRAIN SIM] Opened scene 1 for you. Press Play; it loads scene 2 itself."
            );
        }
    }
}
