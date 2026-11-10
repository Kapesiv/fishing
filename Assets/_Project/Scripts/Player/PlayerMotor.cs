using UnityEngine;

namespace Stillwater.Player
{
    /// <summary>
    /// Grounded character movement on top of CharacterController.
    /// Consumes PlayerInputReader data only - knows nothing about keyboards,
    /// gamepads or network sources.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public class PlayerMotor : MonoBehaviour
    {
        [Header("Movement")]
        [SerializeField] private float moveSpeed = 5f;
        [SerializeField] private float rotationSpeed = 12f;
        [SerializeField] private float gravity = -20f;
        [SerializeField] private float jumpHeight = 1.4f;

        [Header("References")]
        [SerializeField] private PlayerInputReader input;
        [SerializeField] private Transform cameraPivot;

        private CharacterController controller;
        private Vector3 velocity;
        private bool isGrounded;

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
        }

        private void Update()
        {
            isGrounded = controller.isGrounded;
            if (isGrounded && velocity.y < 0f)
                velocity.y = -2f;

            Vector3 moveDirection = CameraRelativeMoveDirection();

            if (moveDirection.sqrMagnitude > 0.001f)
            {
                Quaternion targetRotation = Quaternion.LookRotation(moveDirection, Vector3.up);
                transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
            }

            Vector3 horizontalMotion = moveDirection * moveSpeed;

            if (input.JumpPressed && isGrounded)
            {
                velocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity);
                input.ConsumeJump();
            }

            velocity.y += gravity * Time.deltaTime;

            Vector3 motion = (horizontalMotion + Vector3.up * velocity.y) * Time.deltaTime;
            controller.Move(motion);
        }

        private Vector3 CameraRelativeMoveDirection()
        {
            Vector2 move = input.MoveInput;
            if (move.sqrMagnitude < 0.0001f) return Vector3.zero;

            Transform camRef = cameraPivot != null ? cameraPivot : transform;
            Vector3 forward = Vector3.ProjectOnPlane(camRef.forward, Vector3.up).normalized;
            Vector3 right = Vector3.ProjectOnPlane(camRef.right, Vector3.up).normalized;

            return (forward * move.y + right * move.x).normalized;
        }

        public bool IsGrounded => isGrounded;
    }
}
