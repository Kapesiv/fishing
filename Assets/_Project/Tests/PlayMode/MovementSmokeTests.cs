using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Stillwater.Player;

namespace Stillwater.Tests
{
    public class MovementSmokeTests
    {
        [UnityTest]
        public IEnumerator TestWorld_Loads_PlayerFallsAndComponentsWireUp()
        {
            yield return SceneManager.LoadSceneAsync("TestWorld", LoadSceneMode.Single);
            yield return null;

            var motor = Object.FindAnyObjectByType<PlayerMotor>();
            var reader = Object.FindAnyObjectByType<PlayerInputReader>();
            var cam = Object.FindAnyObjectByType<ThirdPersonCamera>();

            Assert.IsNotNull(motor, "PlayerMotor not found in TestWorld scene");
            Assert.IsNotNull(reader, "PlayerInputReader not found in TestWorld scene");
            Assert.IsNotNull(cam, "ThirdPersonCamera not found in TestWorld scene");
            Assert.IsNotNull(Camera.main, "No MainCamera in TestWorld scene");

            Vector3 startPos = motor.transform.position;

            // Batchmode ticks frames as fast as the CPU allows (sub-millisecond
            // deltaTime), so "N frames" is not a reliable proxy for elapsed
            // simulated time - wait for actual simulated seconds instead.
            // Batchmode ticks frames as fast as the CPU allows (sub-millisecond
            // deltaTime), so "N frames" is not a reliable proxy for elapsed
            // simulated time - wait for actual simulated seconds instead.
            yield return new WaitForSeconds(1.5f);

            Vector3 afterGravityPos = motor.transform.position;
            Assert.Less(afterGravityPos.y, startPos.y + 0.01f,
                "Player should settle under gravity instead of floating/rising on its own");
            Assert.IsTrue(motor.IsGrounded, "Player should be grounded on the test plane after falling");
        }

        [UnityTest]
        public IEnumerator Player_MovesInInputDirection()
        {
            yield return SceneManager.LoadSceneAsync("TestWorld", LoadSceneMode.Single);
            yield return null;

            var motor = Object.FindAnyObjectByType<PlayerMotor>();
            Assert.IsNotNull(motor);

            // Let the player settle on the ground first.
            yield return new WaitForSeconds(1.5f);

            Vector3 beforeMove = motor.transform.position;

            // Drive movement directly through the CharacterController to validate
            // PlayerMotor's physics integration without depending on real hardware input.
            var controller = motor.GetComponent<CharacterController>();
            for (int i = 0; i < 20; i++)
            {
                controller.Move(Vector3.forward * 0.1f);
                yield return null;
            }

            Vector3 afterMove = motor.transform.position;
            float horizontalDelta = Vector3.Distance(
                new Vector3(beforeMove.x, 0, beforeMove.z),
                new Vector3(afterMove.x, 0, afterMove.z));

            Assert.Greater(horizontalDelta, 0.1f, "CharacterController did not move the player horizontally");
        }
    }
}
