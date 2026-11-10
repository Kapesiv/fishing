using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Stillwater.Fish;
using Stillwater.Fishing;

namespace Stillwater.Tests
{
    public class FishingSmokeTests
    {
        private GameObject hookInstance;
        private GameObject fishInstance;

        [TearDown]
        public void TearDown()
        {
            if (hookInstance != null) Object.Destroy(hookInstance);
            if (fishInstance != null) Object.Destroy(fishInstance);
        }

        [UnityTest]
        public IEnumerator Hook_LaunchedAboveWater_LandsAndSettlesAtSurface()
        {
            yield return SceneManager.LoadSceneAsync("TestWorld", LoadSceneMode.Single);
            yield return null;

            var water = GameObject.FindGameObjectWithTag("Water");
            Assert.IsNotNull(water, "No Water-tagged object found in TestWorld scene");

            var rodInScene = Object.FindAnyObjectByType<FishingRod>();
            Assert.IsNotNull(rodInScene, "No FishingRod found in TestWorld scene");

            hookInstance = new GameObject("TestHook");
            var rb = hookInstance.AddComponent<Rigidbody>();
            hookInstance.AddComponent<SphereCollider>().radius = 0.08f;
            var hook = hookInstance.AddComponent<FishingHook>();

            hookInstance.transform.position = water.transform.position + Vector3.up * 3f;
            hook.Launch(Vector3.zero);

            float elapsed = 0f;
            while (elapsed < 2f && hook.State != HookState.InWater)
            {
                yield return null;
                elapsed += Time.deltaTime;
            }

            Assert.AreEqual(HookState.InWater, hook.State, "Hook never transitioned to InWater after falling onto the water trigger");
            Assert.IsTrue(float.IsFinite(hookInstance.transform.position.y), "Hook position became non-finite");
        }

        [UnityTest]
        public IEnumerator HookedFish_StrugglesWithoutNaN_AndCanBeReeledToCatchDistance()
        {
            yield return SceneManager.LoadSceneAsync("TestWorld", LoadSceneMode.Single);
            yield return null;

            var species = Resources.FindObjectsOfTypeAll<FishSpeciesConfig>();
            Assert.Greater(species.Length, 0, "No FishSpeciesConfig asset loaded in scene/project");

            hookInstance = new GameObject("TestHook");
            hookInstance.AddComponent<Rigidbody>().isKinematic = true;
            hookInstance.AddComponent<SphereCollider>().radius = 0.08f;
            var hook = hookInstance.AddComponent<FishingHook>();
            hookInstance.transform.position = new Vector3(0f, 0.5f, 0f);

            var existingFish = Object.FindAnyObjectByType<FishBehaviour>();
            Assert.IsNotNull(existingFish, "No FishBehaviour instance found in TestWorld scene");
            fishInstance = existingFish.gameObject;
            fishInstance.transform.position = hookInstance.transform.position + Vector3.right * 0.5f;

            bool bit = existingFish.TryBite(hook);
            Assert.IsTrue(bit, "FishBehaviour.TryBite returned false for an idle fish");

            // Let the leash + struggle forces run for a bit; this is where NaN/instability
            // would show up if the force math or random jerk direction is malformed.
            yield return new WaitForSeconds(1f);

            Vector3 fishPos = fishInstance.transform.position;
            Assert.IsTrue(float.IsFinite(fishPos.x) && float.IsFinite(fishPos.y) && float.IsFinite(fishPos.z),
                "Fish position became non-finite while hooked (NaN in leash/struggle force math)");

            // Simulate reeling: drag the hook toward a fixed "rod tip" and confirm the fish
            // (dragged via the leash force) ends up close to it too. Bound by elapsed
            // simulated time, not frame count - batchmode frames can be sub-millisecond,
            // so a fixed iteration count is not a reliable proxy for elapsed physics time
            // (see MovementSmokeTests for the same lesson learned on PlayerMotor).
            Vector3 rodTipPos = new Vector3(0f, 1f, -3f);
            float reelElapsed = 0f;
            while (reelElapsed < 5f && Vector3.Distance(hookInstance.transform.position, rodTipPos) > 0.1f)
            {
                hook.MoveToward(rodTipPos, 2.5f * Time.deltaTime);
                yield return null;
                reelElapsed += Time.deltaTime;
            }

            float hookToRodTip = Vector3.Distance(hookInstance.transform.position, rodTipPos);
            Assert.Less(hookToRodTip, 0.1f, "Hook was not dragged to the rod tip by repeated MoveToward calls");

            float fishToHook = Vector3.Distance(fishInstance.transform.position, hookInstance.transform.position);
            Assert.Less(fishToHook, 2f, "Hooked fish was not dragged along with the hook during reeling");
        }
    }
}
