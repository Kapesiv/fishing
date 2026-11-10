using UnityEngine;

namespace Stillwater.Fish
{
    [CreateAssetMenu(fileName = "FishSpecies_", menuName = "Stillwater/Fish Species Config")]
    public class FishSpeciesConfig : ScriptableObject
    {
        [Header("Idle swimming")]
        public float swimSpeed = 1.5f;
        public float wanderRadius = 3f;

        [Header("Biting")]
        [Tooltip("How close a resting hook must be for this fish to notice it, in meters.")]
        public float biteDetectionRadius = 2f;
        [Tooltip("Chance per second to bite once a hook is in detection range.")]
        public float biteChancePerSecond = 0.5f;

        [Header("Struggle (once hooked)")]
        public float struggleForce = 6f;
        public float struggleInterval = 0.4f;
        [Tooltip("How strongly this fish resists being pulled toward the hook's leash point.")]
        public float leashForce = 4f;
        [Tooltip("The fish is physically tethered to the hook by the line - it can never " +
                 "drift farther than this, no matter how hard it struggles.")]
        public float maxTetherDistance = 1.2f;
    }
}
