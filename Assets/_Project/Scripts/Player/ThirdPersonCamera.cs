using UnityEngine;

namespace Stillwater.Player
{
    /// <summary>
    /// Manual orbit-follow camera rig. No Cinemachine dependency yet to keep
    /// the first prototype lean - swap the implementation later if a pulled-in
    /// feature (collision-aware boom, framing) is worth the dependency.
    ///
    /// The rig is the "cameraPivot" PlayerMotor reads for move direction, so
    /// switching to first-person later only means repositioning/disabling this
    /// rig, not touching movement code.
    /// </summary>
    public class ThirdPersonCamera : MonoBehaviour
    {
        [SerializeField] private PlayerInputReader input;
        [SerializeField] private Transform target;
        [SerializeField] private float distance = 5f;
        [SerializeField] private float height = 1.6f;
        [SerializeField] private float sensitivity = 0.15f;
        [SerializeField] private float minPitch = -30f;
        [SerializeField] private float maxPitch = 60f;

        private float yaw;
        private float pitch = 15f;

        private void LateUpdate()
        {
            if (target == null) return;

            yaw += input.LookInput.x * sensitivity;
            pitch -= input.LookInput.y * sensitivity;
            pitch = Mathf.Clamp(pitch, minPitch, maxPitch);

            Quaternion rotation = Quaternion.Euler(pitch, yaw, 0f);
            Vector3 focusPoint = target.position + Vector3.up * height;
            Vector3 desiredPosition = focusPoint - rotation * Vector3.forward * distance;

            transform.position = desiredPosition;
            transform.rotation = rotation;
        }
    }
}
