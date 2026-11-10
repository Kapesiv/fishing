using UnityEngine;
using Stillwater.Fish;

namespace Stillwater.Fishing
{
    public enum HookState { Flying, InWater, Hooked }

    [RequireComponent(typeof(Rigidbody))]
    public class FishingHook : MonoBehaviour
    {
        [SerializeField] private float biteCheckInterval = 0.25f;
        [SerializeField] private float waterSurfaceOffset = -0.1f;

        private Rigidbody body;
        private HookState state;
        private float biteCheckTimer;
        private FishBehaviour hookedFish;
        private float waterSurfaceY;

        public HookState State => state;
        public FishBehaviour HookedFish => hookedFish;

        private void Awake()
        {
            body = GetComponent<Rigidbody>();
            state = HookState.Flying;
        }

        public void Launch(Vector3 velocity)
        {
            state = HookState.Flying;
            body.isKinematic = false;
            body.useGravity = true;
            body.linearVelocity = velocity;
        }

        private void OnTriggerEnter(Collider other)
        {
            if (state == HookState.Flying && other.CompareTag("Water"))
                EnterWater(other);
        }

        private void EnterWater(Collider waterCollider)
        {
            state = HookState.InWater;
            body.useGravity = false;
            body.linearVelocity = Vector3.zero;
            body.isKinematic = true;
            waterSurfaceY = waterCollider.bounds.max.y;

            Vector3 pos = transform.position;
            pos.y = waterSurfaceY + waterSurfaceOffset;
            transform.position = pos;
        }

        private void FixedUpdate()
        {
            if (state != HookState.InWater) return;

            biteCheckTimer -= Time.fixedDeltaTime;
            if (biteCheckTimer <= 0f)
            {
                biteCheckTimer = biteCheckInterval;
                TryFindBite();
            }
        }

        private void TryFindBite()
        {
            var candidates = Physics.OverlapSphere(transform.position, LargestDetectionRadius());
            foreach (var col in candidates)
            {
                var fish = col.GetComponent<FishBehaviour>();
                if (fish == null || !fish.IsAvailableToBite) continue;

                var species = fish.Species;
                float distance = Vector3.Distance(transform.position, fish.transform.position);
                if (distance > species.biteDetectionRadius) continue;

                if (Random.value <= species.biteChancePerSecond * biteCheckInterval)
                {
                    if (fish.TryBite(this))
                    {
                        hookedFish = fish;
                        state = HookState.Hooked;
                        return;
                    }
                }
            }
        }

        private float LargestDetectionRadius()
        {
            // Cheap upper bound for the OverlapSphere query; per-fish species radius
            // still gates the actual bite roll above.
            return 5f;
        }

        /// Called by FishingRod while reeling, to drag the hook (and whatever is
        /// attached to it) toward the rod tip.
        public void MoveToward(Vector3 targetPosition, float maxDistanceDelta)
        {
            transform.position = Vector3.MoveTowards(transform.position, targetPosition, maxDistanceDelta);
        }

        public void ReleaseFish()
        {
            if (hookedFish != null)
                hookedFish.Release();
            hookedFish = null;
            state = HookState.InWater;
        }
    }
}
