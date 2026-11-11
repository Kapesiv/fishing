# Open-source references (checked 2026-11)

Reusable code and assets so we don't rebuild what already exists. Stars and licenses were verified via the GitHub API.
**License rule:** MIT / Apache / CC0 / Unlicense = may copy. GPL = use as a tool only, don't paste its code into our scripts.
Unity Companion = OK inside Unity projects. No license = ideas only.
**Warning:** repos named after "How to Fish" (trainers, mod menus, "companion apps") are spam or possibly malware. Never download them.

## Art style target (How to Fish / Dredge)
- Chunky low-poly, flat colors, no detail textures, a few big shapes, oversized roofs.
- One vendor building and one landmark per area; big readable props, little clutter.
- Our version: keep the dark-fantasy palette (ART_DIRECTION.md) and borrow the simplicity.

## Blender (map generator)
| Repo | License | Use |
|---|---|---|
| github.com/ranjian0/building_tools | MIT | bmesh walls, windows, doors, roofs, stairs: base for cabins, shop, boathouse |
| github.com/ozanzeng/blender-LPM-skill | MIT | flat-shaded palette low-poly assets for Unity (tested on Blender 5.2) |
| github.com/danielgruginski/MedievalVillageKit | CC0 | procedural stylized village buildings + terrain |
| github.com/EdyJ/blender-to-unity-fbx-exporter | MIT | correct axes and scale for Unity FBX export |
| github.com/CommanderFoo/blender-low-poly-rock | MIT | low-poly rock recipe |
| github.com/Colosyn/LOD-Architect-Lite | MIT | LODs with `_LOD0/_LOD1` naming |
| github.com/friggog/tree-gen | GPL-3 (tool) | parametric trees |
| github.com/GitMay3D/OpenScatter | GPL-3 (tool) | Geometry Nodes scatter |

Unity FBX export settings: Scale 1, "FBX All", Forward -Z, Up Y, Apply Transform, Smoothing = Face, LODs named `_LODn`.

## Free assets (CC0 unless noted)
- **KayKit** (kaylousberg.com): Forest Nature Pack, Halloween Bits. One shared gradient atlas = the flat-color workflow.
- **Kenney** (kenney.nl): Survival, Pirate, Watercraft, Fantasy Town and Graveyard kits.
- **Quaternius** (quaternius.com): Animated Fish Pack, Survival Pack, Ships, Medieval Village MegaKit (part free).
- **Poly Pizza** (poly.pizza): search engine for the packs above. "Poly by Google" models are CC-BY (credit required).
- **Poly Haven / ambientCG**: HDRIs for dusk and night skies.
- **Palette workflow guides:** Imphenzia PixPal, wintermutedigital.netlify.app/post/lowpoly-colour-palettes
- **Lists:** github.com/madjin/awesome-cc0
- **Missing:** no free dock or boathouse kit; build them ourselves.

## Unity: fishing
| Repo | License | Use |
|---|---|---|
| github.com/Kevin-Kwan/Unity3D-FishingRodMotion | MIT | cast arc, rod bend, line and reel |
| github.com/GaryMcWhorter/Verlet-Chain-Unity | MIT | fishing line (Verlet) |
| github.com/jongallant/Unity-Verlet-Rope | MIT | small rope with LineRenderer |
| github.com/littensy/fishing-minigame | MIT (Luau) | reel bar minigame logic, easy to port |
| github.com/iiafosh/fosh-and-fish | MIT (Godot) | catch, sell, upgrade loop |
| github.com/mrbid/TuxFishing | MIT (C) | whole small low-poly fishing game |
| github.com/Altrabird/Pancing | none | rod tension and bite scoring ideas, Unity 6 |

## Unity: water, boats, look
| Repo | License | Use |
|---|---|---|
| github.com/Unity-Technologies/BoatAttack | Unity Companion | URP water and boat buoyancy |
| github.com/dbrizov/Unity-WaterBuoyancy | MIT | simple buoyancy for bobber and boats |
| github.com/IronWarrior/ToonWaterShader | Unlicense | toon water (depth colors, foam), port to Shader Graph |
| github.com/ColinLeung-NiloCat/UnityURPToonLitShaderExample | MIT | toon or flat lit shader + outline |
| github.com/CristianQiu/Unity-URP-Volumetric-Light | MIT | volumetric fog and light, **Unity 6** |
| github.com/sinnwrig/URP-Fog-Volumes | MIT | local fog on the lake and in the forest |
| github.com/Kodrin/URP-PSX, github.com/Colby-O2/VNTG | MIT / Unlicense | optional PS1 horror look |
| github.com/jiaozi158/UnityPhysicallyBasedSkyURP | MIT | sky for the day-night cycle |
| github.com/chrisnolet/QuickOutline | MIT | highlight interactable objects |

Note: Unity 6 URP uses Render Graph, so old renderer features need porting.

## Unity: player, co-op, systems
| Repo | License | Use |
|---|---|---|
| github.com/Hertzole/gold-player | MIT | FPS controller |
| github.com/sergioabreu-g/active-ragdolls | Apache-2.0 | wobbly co-op physics feel |
| github.com/Unity-Technologies/com.unity.multiplayer.samples.coop | Unity Companion | Boss Room co-op template, Unity 6000.0 |
| github.com/Unity-Technologies/multiplayer-community-contributions | MIT | Steam transport for Netcode |
| github.com/Facepunch/Facepunch.Steamworks | MIT | Steam lobbies |
| github.com/Metater/MetaVoiceChat | MIT | proximity voice chat |
| github.com/UnityTechnologies/open-project-1 | Apache-2.0 | ScriptableObject inventory, quests, save |
| github.com/ashblue/unity-quest-journal | MIT | quests |

## Later: horror and AI (not building yet)
- github.com/crashkonijn/GOAP (Apache-2.0), github.com/ashblue/fluid-behavior-tree (MIT): creature AI
- github.com/SebLague/Field-of-View (MIT): line of sight for stalker AI
- github.com/FrictionalGames/AmnesiaTheDarkDescent (GPL-3): design reference for sanity and the lantern; don't copy code
- No good open-source Unity flashlight, sanity or event systems exist; write our own (small).
