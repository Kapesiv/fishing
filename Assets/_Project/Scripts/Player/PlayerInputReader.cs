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
        public Vector2 MoveInput { get; private set; }
        public Vector2 LookInput { get; private set; }
        public bool JumpPressed { get; private set; }
        public bool PrimaryActionHeld { get; private set; }

        public void OnMove(InputAction.CallbackContext ctx) => MoveInput = ctx.ReadValue<Vector2>();
        public void OnLook(InputAction.CallbackContext ctx) => LookInput = ctx.ReadValue<Vector2>();
        public void OnPrimaryAction(InputAction.CallbackContext ctx) => PrimaryActionHeld = ctx.ReadValueAsButton();

        public void OnJump(InputAction.CallbackContext ctx)
        {
            if (ctx.performed) JumpPressed = true;
        }

        /// Call once per FixedUpdate after the motor has consumed the jump flag.
        public void ConsumeJump() => JumpPressed = false;
    }
}
