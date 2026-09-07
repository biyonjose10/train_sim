using UnityEngine;

public class Signal1Trigger : MonoBehaviour
{
    public GameObject redLight;
    public GameObject yellowLight;

    private void OnTriggerEnter(Collider other)
    {
        Debug.Log("SOMETHING ENTERED SIGNAL 1 TRIGGER: " + other.gameObject.name);

        if (other.CompareTag("Train"))
        {
            Debug.Log("TRAIN DETECTED! Changing Signal 1 to RED.");

            if (redLight != null)
                redLight.SetActive(true);

            if (yellowLight != null)
                yellowLight.SetActive(false);
        }
    }
}