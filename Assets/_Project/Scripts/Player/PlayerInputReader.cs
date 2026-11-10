using UnityEngine;
using UnityEngine.InputSystem;

namespace Stillwater.Player
{
    /// <summary>
    /// Reads raw Input System events and exposes them as plain data.
    /// Nothing downstream (PlayerMotor, FishingRod, ...) should talk to the
    /// Input System directly - this is the single seam where a future
    /// networked/remote input source can be swapped in without touching
    /// gameplay code.
    /// </summary>
    public class PlayerInputReader : MonoBehaviour
    {
        [SerializeField] private InputActionAsset actions;
        [SerializeField] private string actionMapName = "Player";

        private InputAction moveAction;
        private InputAction lookAction;
        private InputAction jumpAction;
        private InputAction primaryAction;

        public Vector2 MoveInput { get; private set; }
        public Vector2 LookInput { get; private set; }
        public bool JumpPressed { get; private set; }
        public bool PrimaryActionHeld { get; private set; }

        private void Awake()
        {
            var map = actions.FindActionMap(actionMapName, throwIfNotFound: true);
            moveAction = map.FindAction("Move");
            lookAction = map.FindAction("Look");
            jumpAction = map.FindAction("Jump");
            primaryAction = map.FindAction("PrimaryAction");
        }

        private void OnEnable()
        {
            moveAction.Enable();
            lookAction.Enable();
            jumpAction.Enable();
            primaryAction.Enable();

            jumpAction.performed += OnJumpPerformed;
            primaryAction.performed += OnPrimaryActionChanged;
            primaryAction.canceled += OnPrimaryActionChanged;
        }

        private void OnDisable()
        {
            jumpAction.performed -= OnJumpPerformed;
            primaryAction.performed -= OnPrimaryActionChanged;
            primaryAction.canceled -= OnPrimaryActionChanged;

            moveAction.Disable();
            lookAction.Disable();
            jumpAction.Disable();
            primaryAction.Disable();
        }

        private void Update()
        {
            MoveInput = moveAction.ReadValue<Vector2>();
            LookInput = lookAction.ReadValue<Vector2>();
        }

        private void OnJumpPerformed(InputAction.CallbackContext ctx) => JumpPressed = true;
        private void OnPrimaryActionChanged(InputAction.CallbackContext ctx) => PrimaryActionHeld = ctx.ReadValueAsButton();

        /// Call once per FixedUpdate after the motor has consumed the jump flag.
        public void ConsumeJump() => JumpPressed = false;
    }
}
