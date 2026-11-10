# STILLWATER — Phase 1 Technical Plan

3D PC co-op-ready fishing adventure. Unity 6, URP, C#. Target feel: ~50%
lighthearted fishing-chaos (How to Fish), ~50% quiet mystery/discovery
(Dredge-like), stylized/low-poly, no photorealism.

## Architecture principles

- **Input → Intent → Simulation** separation from day one, even with zero
  networking code. `PlayerInputReader` only produces plain data
  (`MoveInput`, `JumpPressed`, ...). Gameplay components (`PlayerMotor`,
  later `FishingRod`) consume that data and never touch the Input System
  directly. This is the seam where a networked input source replaces the
  local one later without rewriting movement/fishing code.
- **ScriptableObject-driven content**: fish species, boat tuning, etc. are
  data assets, not hardcoded values, so design iteration doesn't require
  code changes.
- **Separation of gameplay / physics / VFX**: a fish's decision logic
  (`FishBehaviour`, future) stays independent of the physics forces it
  applies and independent of any particle/visual feedback.
- No paid assets. Placeholder primitives/low-poly stand-ins until final art.
- Prefer small testable MonoBehaviours over one large manager class.
- Physics-affecting movement (`CharacterController.Move`, gravity
  integration, ground checks) runs in `FixedUpdate`, not `Update`. Purely
  visual interpolation (facing rotation, camera) runs in `Update`/`LateUpdate`.

## Folder structure

```
Assets/_Project/
  Scripts/
    Stillwater.Gameplay.asmdef
    Player/    movement, camera, input reading
    Fishing/   rod, line, cast, reel            (Phase 2)
    Fish/      behaviour + species config        (Phase 2)
    Boat/      boat controller                   (Phase 3)
    Core/      shared gameplay interfaces
    UI/        HUD                                (Phase 3)
  Tests/PlayMode/   headless play-mode smoke tests
  Prefabs/     Player, Fish, Environment
  ScriptableObjects/FishSpecies/
  Art/Placeholder/
  Scenes/      TestWorld.unity
  Settings/    InputActions, URP
```

## Current status: Phase 1 complete and verified

Unity 6.000.0.85f2 (LTS) is installed, project is set up with URP + the new
Input System, and the first playable loop (movement, jump, third-person
camera, test world) is built, wired, and passing automated tests.

### What exists

- `Player/PlayerInputReader.cs` — owns the Input System interaction
  directly (subscribes to `InputAction` callbacks itself; no `PlayerInput`
  UnityEvent wiring needed). Exposes `MoveInput`, `LookInput`,
  `JumpPressed`, `PrimaryActionHeld` as plain data.
- `Player/PlayerMotor.cs` — CharacterController-based move/jump,
  camera-relative movement. Ground state and movement integration run in
  `FixedUpdate`; facing rotation runs in `Update`.
- `Player/ThirdPersonCamera.cs` — manual orbit-follow rig (no Cinemachine
  dependency; doubles as the "forward" reference `PlayerMotor` moves
  relative to, so first-person later is a camera-rig swap, not a movement
  rewrite).
- `Settings/InputActions/StillwaterControls.inputactions` — Player map with
  Move/Look/Jump/PrimaryAction.
- `Settings/URP/` — URP pipeline + renderer + global settings assets, wired
  as the project's default render pipeline.
- `Prefabs/Player/Player.prefab`, `Prefabs/Player/CameraRig.prefab`.
- `Scenes/TestWorld.unity` — ground plane, a few test boxes, directional
  light, Player + CameraRig instances, fully wired.
- `Tests/PlayMode/MovementSmokeTests.cs` — two headless PlayMode tests
  (`dotnet`/Unity Test Framework): player settles under gravity and reports
  grounded after falling; CharacterController actually moves the player
  horizontally. Run via:
  ```
  /Applications/Unity/Hub/Editor/6000.0.85f2/Unity.app/Contents/MacOS/Unity \
    -batchmode -nographics -projectPath /Users/kasperi/fishing \
    -runTests -testPlatform PlayMode -testResults <path>.xml -logFile -
  ```

### Two real bugs found and fixed via the automated tests

1. **`CharacterController.isGrounded` is unreliable at rest.** It only
   reflects whether the *previous* `Move()` call registered a collision
   below, and at near-zero vertical velocity it flickers `false` most
   frames — jump input gated on it would have been unreliable in the
   shipped game, not just in tests. Fixed with a raycast-based ground
   check (`PlayerMotor.CheckGrounded`) that starts the ray inside the
   capsule (PhysX doesn't report a hit against the collider the ray
   originates in) and ignores a hit if it somehow is the controller itself.
2. **Movement integrated in `Update()` can silently stall at very high
   frame rates.** With sub-millisecond `deltaTime` (observed in headless
   batch runs, but equally possible on an uncapped/high-refresh-rate
   display), `velocity * deltaTime` per frame rounds below
   `CharacterController.Move()`'s minimum-move threshold and gets dropped
   — velocity keeps integrating correctly in script, but the character
   barely moves. Fixed by moving all `CharacterController.Move` and gravity
   integration into `FixedUpdate`, which has a constant step
   (`Time.fixedDeltaTime`, 0.02s) regardless of render frame rate.

### Manual verification still worth doing

The automated tests cover physics correctness (falls, settles, grounds,
moves) but not feel or real input devices. Worth a manual Play Mode pass in
the Editor to judge: camera feel with real mouse input, movement
responsiveness, jump height/arc feel.

## Phase 2: fishing core (complete and verified)

Cast → wait → bite → reel → catch, against one placeholder fish species.

### What exists

- `Fish/FishSpeciesConfig.cs` — ScriptableObject (swim speed, wander
  radius, bite detection radius/chance, struggle force/interval, leash
  force, max tether distance). `PerchConfig.asset` is the one placeholder
  species.
- `Fish/FishBehaviour.cs` — Idle (wanders around a home point) / Hooked
  (leashed toward the hook with continuous pull + periodic random struggle
  impulses, hard-clamped to `maxTetherDistance` from the hook) / Caught.
- `Fishing/FishingHook.cs` — Flying (launched projectile) → InWater
  (detected via a `Water`-tagged trigger collider, settles at the surface)
  → Hooked (a fish bit). Bite rolls happen per-fish, gated by that species'
  own detection radius and chance-per-second.
- `Fishing/FishingLine.cs` — pure visual `LineRenderer` with a sagging
  midpoint between rod tip and hook; no physics.
- `Fishing/FishingRod.cs` — state machine (Idle → Charging → Flying →
  Waiting → Hooked → back to Idle on catch). Hold `PrimaryAction` to charge
  cast power, release to cast; hold `Reel` to pull the hook (and whatever
  is hooked) toward the rod tip; reaching `catchDistance` completes the
  catch and resets.
- New `Reel` input action (right mouse / `E` / gamepad East) added to
  `StillwaterControls.inputactions`.
- `Player.prefab` now carries a `FishingRod` + `FishingLine` + a `RodTip`
  child transform.
- `TestWorld.unity` has a `Water`-tagged trigger volume and one `Perch`
  instance swimming in it.
- `Tests/PlayMode/FishingSmokeTests.cs` — hook falls onto water and settles
  in `InWater` state; a hooked fish's position stays finite under
  leash+struggle forces and gets dragged along when the hook is reeled to
  a target point.

### Two real bugs found and fixed via the automated tests

1. **Struggle could out-pull the leash indefinitely.** Random struggle
   impulses (instantaneous velocity kicks) were large enough relative to
   the continuous leash pull that a hooked fish could drift farther and
   farther from the hook forever — reeling would never be able to land a
   fish in the shipped game, not just in the test. Fixed by hard-clamping
   the fish to `maxTetherDistance` from the hook every `FixedUpdate`: it
   can still thrash around inside that radius, but the line physically
   can't stretch past it.
2. **Test-only: frame-count loops instead of elapsed-time loops.** Reused
   the exact mistake Phase 1 already caught once — driving the reeling
   simulation with `for (i < N) yield return null` instead of a
   `Time.deltaTime`-bounded loop. In headless batchmode with sub-ms
   frames, hundreds of iterations can complete before any meaningful
   physics time elapses. Not a gameplay bug, but worth noting since it's
   the second time this exact pattern caused a false read.

### Manual verification still worth doing

Cast arc/power feel, whether the bite delay feels fair, whether reeling
feels like a tug-of-war rather than a non-event. The automated tests only
prove the physics doesn't break or stall.

## What's still missing

- Second and third fish species (currently one placeholder, "Perch").
- Boat controller.
- Ragdoll-on-impact.
- HUD (cast power meter, prompts, catch feedback beyond a console log).
- Fishing village / dock / lake dressing beyond a flat test plane + one
  water trigger volume.

## Next development phase

Add HUD feedback for the fishing loop (cast power meter, "something's
biting!" prompt, catch confirmation) so the loop is legible without
reading the Console - then add 1-2 more fish species to validate the
ScriptableObject-driven config actually produces varied-feeling fish.
