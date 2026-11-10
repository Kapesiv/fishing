using UnityEngine;
using Stillwater.Player;

namespace Stillwater.Fishing
{
    public enum RodState { Idle, Charging, Flying, Waiting, Hooked, Caught }

    public class FishingRod : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private PlayerInputReader input;
        [SerializeField] private Transform rodTip;
        [SerializeField] private Transform aimReference;
        [SerializeField] private FishingHook hookPrefab;
        [SerializeField] private FishingLine line;

        [Header("Casting")]
        [SerializeField] private float minCastForce = 3f;
        [SerializeField] private float maxCastForce = 10f;
        [SerializeField] private float chargeDuration = 1.2f;
        [SerializeField] private float castUpwardAngle = 20f;

        [Header("Reeling")]
        [SerializeField] private float reelSpeed = 2.5f;
        [SerializeField] private float catchDistance = 0.6f;

        private RodState state;
        private float chargePower;
        private FishingHook activeHook;
        private bool reelHeldLastFrame;

        public RodState State => state;
        public float ChargePower => chargePower;

        private void Update()
        {
            switch (state)
            {
                case RodState.Idle:
                    if (input.PrimaryActionHeld)
                        state = RodState.Charging;
                    break;

                case RodState.Charging:
                    chargePower = Mathf.Clamp01(chargePower + Time.deltaTime / chargeDuration);
                    if (!input.PrimaryActionHeld)
                        Cast();
                    break;

                case RodState.Flying:
                    if (activeHook.State == HookState.InWater)
                        state = RodState.Waiting;
                    break;

                case RodState.Waiting:
                    if (activeHook.State == HookState.Hooked)
                        state = RodState.Hooked;
                    else if (input.ReelHeld)
                        RetrieveEmptyHook();
                    break;

                case RodState.Hooked:
                    TickHooked();
                    break;
            }
        }

        private void Cast()
        {
            Vector3 origin = rodTip.position;
            Transform aim = aimReference != null ? aimReference : transform;
            Vector3 direction = Quaternion.AngleAxis(-castUpwardAngle, aim.right) * aim.forward;

            activeHook = Instantiate(hookPrefab, origin, Quaternion.identity);
            float force = Mathf.Lerp(minCastForce, maxCastForce, chargePower);
            activeHook.Launch(direction.normalized * force);

            line.SetHook(activeHook.transform);
            chargePower = 0f;
            state = RodState.Flying;
        }

        private void TickHooked()
        {
            if (!input.ReelHeld)
                return;

            activeHook.MoveToward(rodTip.position, reelSpeed * Time.deltaTime);

            float distance = Vector3.Distance(activeHook.transform.position, rodTip.position);
            if (distance <= catchDistance)
                CompleteCatch();
        }

        private void CompleteCatch()
        {
            var fish = activeHook.HookedFish;
            if (fish != null)
            {
                fish.MarkCaught();
                Debug.Log($"Caught a {fish.Species.name}!");
                Destroy(fish.gameObject, 0.1f);
            }

            ResetRod();
        }

        private void RetrieveEmptyHook()
        {
            activeHook.MoveToward(rodTip.position, reelSpeed * Time.deltaTime);
            if (Vector3.Distance(activeHook.transform.position, rodTip.position) <= catchDistance)
                ResetRod();
        }

        private void ResetRod()
        {
            if (activeHook != null)
                Destroy(activeHook.gameObject);
            activeHook = null;
            line.SetHook(null);
            state = RodState.Idle;
        }
    }
}
