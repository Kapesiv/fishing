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
        [SerializeField] private float groundCheckExtraDistance = 0.2f;

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
            // Facing rotation is purely visual - fine to update every render frame.
            Vector3 moveDirection = CameraRelativeMoveDirection();
            if (moveDirection.sqrMagnitude > 0.001f)
            {
                Quaternion targetRotation = Quaternion.LookRotation(moveDirection, Vector3.up);
                transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
            }
        }

        private void FixedUpdate()
        {
            // CharacterController.Move must run on the fixed physics step: at very
            // high uncapped frame rates, Update's deltaTime shrinks enough that
            // velocity*deltaTime rounds down to a sub-threshold distance Move()
            // silently drops, so the character stops falling/moving despite
            // velocity integrating correctly. FixedUpdate keeps the step size
            // constant (Time.fixedDeltaTime) regardless of render frame rate.
            //
            // CharacterController.isGrounded only reflects whether the last Move()
            // registered a collision below - at rest with near-zero vertical motion
            // it flickers false most frames. A raycast from inside the capsule
            // (which PhysX never reports a hit against for its own collider) gives
            // a stable resting-state check that jump input can rely on.
            isGrounded = CheckGrounded();
            if (isGrounded && velocity.y < 0f)
                velocity.y = -2f;

            Vector3 horizontalMotion = CameraRelativeMoveDirection() * moveSpeed;

            if (input.JumpPressed && isGrounded)
            {
                velocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity);
                input.ConsumeJump();
            }

            velocity.y += gravity * Time.fixedDeltaTime;

            Vector3 motion = (horizontalMotion + Vector3.up * velocity.y) * Time.fixedDeltaTime;
            controller.Move(motion);
        }

        private bool CheckGrounded()
        {
            Vector3 origin = transform.position + controller.center;
            float maxDistance = controller.height / 2f + groundCheckExtraDistance;
            if (Physics.Raycast(origin, Vector3.down, out RaycastHit hit, maxDistance, ~0, QueryTriggerInteraction.Ignore))
            {
                return hit.collider != (Collider)controller;
            }
            return false;
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
