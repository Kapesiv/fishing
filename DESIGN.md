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

## What's still missing

- Fishing system (rod, cast, line, reel, fish bite).
- Fish species + behaviour (3 fish for first tests).
- Boat controller.
- Ragdoll-on-impact.
- HUD.
- Fishing village / dock / lake dressing beyond a flat test plane.

## Next development phase

Build the **physics-based fishing core** (rod bend, line, cast,
hook-fish-grab, reel) against a single placeholder fish, before adding
species variety or the boat.
