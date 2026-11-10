using UnityEngine;
using Stillwater.Fishing;

namespace Stillwater.Fish
{
    [RequireComponent(typeof(Rigidbody))]
    public class FishBehaviour : MonoBehaviour
    {
        private enum State { Idle, Hooked, Caught }

        [SerializeField] private FishSpeciesConfig species;

        private Rigidbody body;
        private State state;
        private Vector3 homePoint;
        private Vector3 wanderTarget;
        private FishingHook hook;
        private float struggleTimer;

        public bool IsAvailableToBite => state == State.Idle;

        private void Awake()
        {
            body = GetComponent<Rigidbody>();
            body.useGravity = false;
            homePoint = transform.position;
            PickNewWanderTarget();
        }

        private void FixedUpdate()
        {
            switch (state)
            {
                case State.Idle:
                    TickIdle();
                    break;
                case State.Hooked:
                    TickHooked();
                    break;
            }
        }

        private void TickIdle()
        {
            Vector3 toTarget = wanderTarget - transform.position;
            if (toTarget.magnitude < 0.3f)
            {
                PickNewWanderTarget();
                return;
            }

            body.linearVelocity = toTarget.normalized * species.swimSpeed;

            if (toTarget.sqrMagnitude > 0.001f)
                transform.rotation = Quaternion.LookRotation(toTarget.normalized, Vector3.up);
        }

        private void TickHooked()
        {
            if (hook == null)
            {
                Release();
                return;
            }

            Vector3 toHook = hook.transform.position - transform.position;
            body.AddForce(toHook.normalized * species.leashForce, ForceMode.Acceleration);

            struggleTimer -= Time.fixedDeltaTime;
            if (struggleTimer <= 0f)
            {
                struggleTimer = species.struggleInterval;
                Vector3 randomJerk = new Vector3(Random.Range(-1f, 1f), Random.Range(0f, 0.6f), Random.Range(-1f, 1f));
                body.AddForce(randomJerk.normalized * species.struggleForce, ForceMode.Impulse);
            }

            // The fish is physically tethered by the line - struggling can look wild,
            // but it can never pull farther from the hook than the line allows. Without
            // this, a random jerk can outrun the leash's continuous pull entirely and
            // the fish becomes impossible to reel in.
            toHook = hook.transform.position - transform.position;
            if (toHook.magnitude > species.maxTetherDistance)
            {
                transform.position = hook.transform.position - toHook.normalized * species.maxTetherDistance;
                body.linearVelocity = Vector3.ClampMagnitude(body.linearVelocity, species.leashForce);
            }
        }

        private void PickNewWanderTarget()
        {
            Vector2 offset = Random.insideUnitCircle * species.wanderRadius;
            wanderTarget = homePoint + new Vector3(offset.x, 0f, offset.y);
        }

        /// Called by FishingHook when it decides this fish has taken the bait.
        public bool TryBite(FishingHook biterHook)
        {
            if (state != State.Idle) return false;

            state = State.Hooked;
            hook = biterHook;
            struggleTimer = species.struggleInterval;
            return true;
        }

        public void MarkCaught()
        {
            state = State.Caught;
            hook = null;
            body.linearVelocity = Vector3.zero;
        }

        public void Release()
        {
            state = State.Idle;
            hook = null;
            PickNewWanderTarget();
        }

        public FishSpeciesConfig Species => species;
    }
}
