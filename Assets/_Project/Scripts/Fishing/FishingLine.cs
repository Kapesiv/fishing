using UnityEngine;

namespace Stillwater.Fishing
{
    /// <summary>
    /// Purely visual. Draws a sagging line between the rod tip and the hook -
    /// no physics simulation, just a lowered midpoint so it doesn't look like a
    /// rigid rod extension.
    /// </summary>
    [RequireComponent(typeof(LineRenderer))]
    public class FishingLine : MonoBehaviour
    {
        [SerializeField] private Transform rodTip;
        [SerializeField] private Transform hook;
        [SerializeField] private float sagPerMeter = 0.05f;

        private LineRenderer line;

        private void Awake()
        {
            line = GetComponent<LineRenderer>();
            line.positionCount = 3;
        }

        private void LateUpdate()
        {
            bool active = rodTip != null && hook != null && hook.gameObject.activeInHierarchy;
            line.enabled = active;
            if (!active) return;

            Vector3 start = rodTip.position;
            Vector3 end = hook.position;
            Vector3 mid = Vector3.Lerp(start, end, 0.5f);
            mid.y -= Vector3.Distance(start, end) * sagPerMeter;

            line.SetPosition(0, start);
            line.SetPosition(1, mid);
            line.SetPosition(2, end);
        }

        public void SetHook(Transform newHook) => hook = newHook;
    }
}
