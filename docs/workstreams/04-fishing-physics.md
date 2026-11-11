# 04 – Fishing & Physics

**Haara:** `feature/fishing-physics` · **Worktree:** `C:\Users\kappu\lureloom\04-fishing-physics`

## Vastuu
- Kalastusmekaniikka: vapa, siima, koukku, heitto, kelaus, tärppi, saalis
- Kalojen käyttäytyminen ja lajit (ScriptableObject-pohjaiset)
- Kalastuksen fysiikka ja tuntuma (vavan taipuminen, kala vetää pelaajaa)
- Veneen fysiikka ja ohjaus (`Scripts/Boat/`)
- Kalastus- ja venetestit

## Omat tiedostot
- `Assets/_Project/Scripts/Fishing/**`, `Scripts/Fish/**`, `Scripts/Boat/**`
- `Assets/_Project/ScriptableObjects/FishSpecies/**`
- `Assets/_Project/Prefabs/Fish/**`, `Prefabs/Fishing/**`
- `Assets/_Project/Tests/PlayMode/FishingSmokeTests.cs` ja uudet kalastus- ja venetestit
- `Assets/_Project/Sandbox/Fishing/**`

## Ei muokkaa
- `Player.prefab`, skenejä, input actioneita eikä `PlayerMotor`ia (06). Jos tarvitset uuden input-actionin tai pelaajaan vaikuttavan voiman (kala vetää hahmoa), tee ehdotus 06:lle.

## Säännöt
- **Säilytä nykyinen toimiva kalastusjärjestelmä ja sen testit** (DESIGN.md, Phase 2). Älä heikennä tetheriä (`maxTetherDistance`) äläkä FixedUpdate-integraatiota.
- Input → Intent → Simulation: kalastus ei lue Input Systemiä suoraan eikä riipu käyttöliittymästä.
- Testeissä käytä aikaan sidottuja silmukoita, ei framemäärää.
- Aja PlayMode-testit ennen PR:ää. Jos Unity ei ole käytettävissä, kerro se.
