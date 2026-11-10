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

## Folder structure

```
Assets/_Project/
  Scripts/
    Player/    movement, camera, input reading
    Fishing/   rod, line, cast, reel            (Phase 2)
    Fish/      behaviour + species config        (Phase 2)
    Boat/      boat controller                   (Phase 3)
    Core/      shared gameplay interfaces
    UI/        HUD                                (Phase 3)
  Prefabs/     Player, Fish, Environment
  ScriptableObjects/FishSpecies/
  Art/Placeholder/
  Scenes/      TestWorld.unity
  Settings/    InputActions, URP
```

## Phase 1 scope (this delivery)

Character movement + third-person camera + a place to stand on. Explicitly
**not** included yet: fishing, fish, boat, ragdoll, HUD — each is its own
phase so we can test one solid system at a time instead of a pile of
half-working ones.

### Scripts delivered

- `Player/PlayerInputReader.cs` — Input System → plain data seam.
- `Player/PlayerMotor.cs` — CharacterController-based move/jump,
  camera-relative movement, grounded check.
- `Player/ThirdPersonCamera.cs` — manual orbit-follow rig (no Cinemachine
  dependency yet; the rig doubles as the "forward" reference `PlayerMotor`
  moves relative to, so switching to first-person later is a camera-rig
  swap, not a movement rewrite).

### Not yet created (needs the Unity Editor, see setup steps below)

- The `.inputactions` asset itself — hand-authoring that JSON by hand is
  fragile across Input System versions; create it in-editor (2 minutes,
  steps below) rather than risk a malformed asset.
- The test scene, Player prefab, and CharacterController/camera wiring.

## Setup steps (do this in Unity once installed)

1. **Install**: Unity Hub → Unity 6 (LTS) → create project, template
   **3D (URP)**, name `Stillwater`.
   - This repo is already a git repo with `Assets/_Project/...` populated.
     Unity Hub's "New Project" dialog creates a *new* project folder under
     whatever "Location" you pick — it won't write into an existing
     non-empty folder. Practical options:
     a) Create the project anywhere temporary, then copy its generated
        `Assets/`, `Packages/`, `ProjectSettings/` folders into
        `/Users/kasperi/fishing`, merging `Assets/_Project` (already here)
        with Unity's generated `Assets/Scenes` etc.
     b) Or create it with Location = `/Users/kasperi` and name `fishing`
        — only works if Unity refuses less strictly than expected; if it
        errors on the existing folder, use (a).
   - Tell me once the project opens and I'll verify the layout.
2. **Package Manager** → confirm **Input System** package is installed
   (URP template usually prompts to switch input handling to "Input System
   Package (New)" — accept and let it restart).
3. **Create Input Actions asset**: `Assets/_Project/Settings/InputActions`
   → right-click → Create → Input Actions → name `StillwaterControls`.
   Open it and add:
   - Action Map `Player`
     - `Move` (Value, Vector2) — bind WASD (2D Vector composite) + left
       gamepad stick.
     - `Look` (Value, Vector2) — bind mouse delta + right gamepad stick.
     - `Jump` (Button) — Space / gamepad South button.
     - `PrimaryAction` (Button) — Left Mouse / gamepad West button
       (reserved for casting in Phase 2).
   - Check "Generate C# Class" **off** for now — we're wiring via
     `PlayerInput` component's Unity Events, not generated code.
4. **Test scene**: `Assets/_Project/Scenes/TestWorld.unity` — flat ground
   plane + a few boxes/ramps to judge movement feel.
5. **Player prefab**: empty GameObject `Player` with:
   - `CharacterController` (radius ~0.4, height ~1.8)
   - `PlayerInputReader`
   - `PlayerMotor` (drag in the `PlayerInputReader`, and the camera rig's
     transform once created)
   - `PlayerInput` component (Unity's, from the Input System package),
     Actions = `StillwaterControls`, Default Map = `Player`, Behavior =
     "Invoke Unity Events" → wire `Move`/`Look`/`Jump`/`PrimaryAction`
     events to the matching methods on `PlayerInputReader`.
   - A simple capsule or placeholder low-poly mesh as a visible child.
6. **Camera rig**: empty GameObject `CameraRig` with `ThirdPersonCamera`
   (target = Player transform, input = the same `PlayerInputReader`) and a
   child `Main Camera`.
7. Press Play, walk with WASD, look with mouse, jump with Space.

## How to test this step

- Player moves in the direction held relative to camera facing.
- Character visually rotates to face movement direction.
- Jump only triggers when grounded; no double-jump, no sinking through
  ground.
- Camera orbits smoothly with mouse, clamped pitch (can't flip upside down).

## What's still missing

- Fishing system (rod, cast, line, reel, fish bite).
- Fish species + behaviour (3 fish for first tests).
- Boat controller.
- Ragdoll-on-impact.
- HUD.
- Fishing village / dock / lake dressing beyond a flat test plane.

## Next development phase

Once movement+camera is verified in-editor: build the **physics-based
fishing core** (rod bend, line, cast, hook-fish-grab, reel) against a single
placeholder fish, before adding species variety or the boat.
