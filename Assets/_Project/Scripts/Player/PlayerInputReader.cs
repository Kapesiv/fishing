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
        private InputAction reelAction;

        public Vector2 MoveInput { get; private set; }
        public Vector2 LookInput { get; private set; }
        public bool JumpPressed { get; private set; }
        public bool PrimaryActionHeld { get; private set; }
        public bool ReelHeld { get; private set; }

        private void Awake()
        {
            var map = actions.FindActionMap(actionMapName, throwIfNotFound: true);
            moveAction = map.FindAction("Move");
            lookAction = map.FindAction("Look");
            jumpAction = map.FindAction("Jump");
            primaryAction = map.FindAction("PrimaryAction");
            reelAction = map.FindAction("Reel");
        }

        private void OnEnable()
        {
            moveAction.Enable();
            lookAction.Enable();
            jumpAction.Enable();
            primaryAction.Enable();
            reelAction.Enable();

            jumpAction.performed += OnJumpPerformed;
            primaryAction.performed += OnPrimaryActionChanged;
            primaryAction.canceled += OnPrimaryActionChanged;
            reelAction.performed += OnReelChanged;
            reelAction.canceled += OnReelChanged;
        }

        private void OnDisable()
        {
            jumpAction.performed -= OnJumpPerformed;
            primaryAction.performed -= OnPrimaryActionChanged;
            primaryAction.canceled -= OnPrimaryActionChanged;
            reelAction.performed -= OnReelChanged;
            reelAction.canceled -= OnReelChanged;

            moveAction.Disable();
            lookAction.Disable();
            jumpAction.Disable();
            primaryAction.Disable();
            reelAction.Disable();
        }

        private void Update()
        {
            MoveInput = moveAction.ReadValue<Vector2>();
            LookInput = lookAction.ReadValue<Vector2>();
        }

        private void OnJumpPerformed(InputAction.CallbackContext ctx) => JumpPressed = true;
        private void OnPrimaryActionChanged(InputAction.CallbackContext ctx) => PrimaryActionHeld = ctx.ReadValueAsButton();
        private void OnReelChanged(InputAction.CallbackContext ctx) => ReelHeld = ctx.ReadValueAsButton();

        /// Call once per FixedUpdate after the motor has consumed the jump flag.
        public void ConsumeJump() => JumpPressed = false;
    }
}
