# STILLWATER — Game Vision

A 3D PC fishing adventure for 1–4 players.

## Vision

STILLWATER combines three things:

1. **How to Fish**-style fun, easy-to-learn fishing.
2. A colorful, soft, stylized 3D world with small cartoon-like characters.
3. The mystery and discovery feeling of **Dredge**, with its own story and world.

The game should feel roughly **50% fun, 50% mystery**.

This is not meant to be a realistic fishing simulator. It should feel light,
fun, and a little chaotic.

## Technology

- Unity 6, C#
- Universal Render Pipeline (URP)
- Unity Input System
- Physics-based interaction for characters and objects
- PC as the primary platform
- Architecture that allows 1–4 player co-op multiplayer to be added later,
  without a major rewrite. No complex networking code until core
  gameplay works — but systems are designed so multiplayer doesn't
  require tearing them up (see "Input → Intent → Simulation" in
  `DESIGN.md`).

## Visual style

- Stylized / low-poly 3D
- Soft shapes, colorful environment
- Beautiful water effects
- Small, characterful cartoon characters
- Warm daylight and atmospheric nights
- No photorealism
- Clear, minimal UI

## First playable prototype

1. A small lake, a dock, and a simple fishing village.
2. A third-person controlled character, with a camera that can later
   switch to first-person.
3. Character movement, jumping, interactions.
4. A physics-based fishing system: casting, hooking a fish, reeling,
   landing it.
5. Three different fish for early testing.
6. A simple ragdoll system that activates on hard collisions.
7. A controllable small boat.
8. A simple HUD.

## Fishing design principles

Fishing has to be fun within the first minute.

Fish can make fast movements, jump, and pull the player. The rod should
visibly bend, and the line should behave believably but in a fun,
game-first way rather than a strictly realistic one.

Physics is allowed to cause unexpected situations, but the player should
always feel like they're in control of the game.

## Technical requirements

- Modular C# components.
- Fish behaviour defined via easily extendable settings (data, not
  hardcoded values).
- Gameplay logic, physics, and visual effects kept separate.
- Don't build unnecessarily complex systems.
- Favor testable, maintainable code.
- No dependency on paid assets.
- Use temporary placeholder 3D models where needed, replaceable later.

## Working approach

Start by checking the current project and dev environment. Build a short
technical plan and a sensible folder structure before writing gameplay
code. Build one working whole at a time — character movement + camera +
a small test world first — rather than trying to implement every feature
at once.

After each step, report: what was built, how to test it in Unity, what's
still missing, and what the next step is.

The goal is an actually playable game, not just a technical demo.

---

See `DESIGN.md` for the technical plan, current implementation status,
and phase-by-phase progress against this vision.
