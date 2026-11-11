# LURELOOM – projektin rakenne ja vastuualueet

## 1. Nykyinen rakenne (tarkistettu 10.11.2026)

```
fishing/                              repo: github.com/Kapesiv/fishing
├─ Assets/_Project/                   Unity 6000.0.85f2, URP, Input System
│  ├─ Scripts/
│  │  ├─ Stillwater.Gameplay.asmdef
│  │  ├─ Player/   PlayerInputReader, PlayerMotor, ThirdPersonCamera
│  │  ├─ Fishing/  FishingRod, FishingLine, FishingHook
│  │  ├─ Fish/     FishBehaviour, FishSpeciesConfig
│  │  ├─ Boat/     (tyhjä)
│  │  ├─ Core/     (tyhjä)
│  │  └─ UI/       (tyhjä)
│  ├─ Tests/PlayMode/   MovementSmokeTests, FishingSmokeTests (+ asmdef)
│  ├─ Prefabs/          Player/, Fish/Perch, Fishing/Hook, Environment/ (tyhjä)
│  ├─ ScriptableObjects/FishSpecies/PerchConfig.asset
│  ├─ Scenes/TestWorld.unity
│  ├─ Settings/         InputActions/StillwaterControls, URP/ (pipeline, renderer, volume)
│  └─ Art/Placeholder/  (tyhjä)
├─ Packages/, ProjectSettings/
├─ Blender/SunshoreBay/               mapin blockout (EI VIELÄ COMMITATTU)
│  ├─ scripts/build_sunshore_bay.py
│  ├─ SunshoreBay_Blockout.blend
│  ├─ renders/
│  └─ README.md
├─ LURELOOM_PRODUCTION_PLAN.md, GAME_DESIGN.md, DESIGN.md, README.md
└─ CLAUDE.md, ART_DIRECTION.md, PROJECT_STRUCTURE.md, docs/   (uudet)
```

Haarat: `main` (9 committia). Lisäksi GitHubissa on haara **`origin/blender-lake-map`** (1 commit: `Tools/Blender/generate_map.py`, toinen mapin generaattori, jota ei ole yhdistetty mainiin). Ks. riskit, kohta 7.

## 2. Tuleva kansiorakenne (lisäykset)

Uudet kansiot luo se alue, joka omistaa ne, ja vasta silloin kun niitä tarvitaan.

```
Blender/
  SunshoreBay/            01 World & Map
  Assets/                 02 Buildings & Nature  (Buildings/, Nature/, Props/, Boats/, scripts/, renders/)
  Characters/             03 Characters & Animation  (Fisher01/, Rig/, Animations/, scripts/, renders/)
Assets/_Project/
  Art/World/              01 (heightmap, maaston referenssit)
  Art/Environment/        02 (viedyt FBX/glTF-mallit + materiaalit)
  Art/Characters/         03 (hahmomallit, rigit)
  Animation/              03 (animaatioklipit, Animator Controllerit)
  Atmosphere/             05 (Scripts/, VFX/, Shaders/, Profiles/ = Volume-profiilit, Skyboxes/)
  Sandbox/<alue>/         jokaisen alueen oma testiskene, ei peliin
  Prefabs/Environment/    06 (prefabit 02:n malleista)
docs/
  workstreams/            alueiden ohjeet
  proposals/              muutosehdotukset toisten alueiden tiedostoihin
```

## 3. Kuusi vastuualuetta

| # | Alue | Haara | Ohje |
|---|---|---|---|
| 01 | World & Map | `feature/world-map` | [docs/workstreams/01-world-map.md](docs/workstreams/01-world-map.md) |
| 02 | Buildings & Nature | `feature/buildings-nature` | [docs/workstreams/02-buildings-nature.md](docs/workstreams/02-buildings-nature.md) |
| 03 | Characters & Animation | `feature/characters-animation` | [docs/workstreams/03-characters-animation.md](docs/workstreams/03-characters-animation.md) |
| 04 | Fishing & Physics | `feature/fishing-physics` | [docs/workstreams/04-fishing-physics.md](docs/workstreams/04-fishing-physics.md) |
| 05 | Atmosphere & Horror | `feature/atmosphere-horror` | [docs/workstreams/05-atmosphere-horror.md](docs/workstreams/05-atmosphere-horror.md) |
| 06 | Unity Integration | `feature/unity-integration` | [docs/workstreams/06-unity-integration.md](docs/workstreams/06-unity-integration.md) |

## 4. Tiedostojen omistajuus

Omistaja on ainoa, joka muokkaa tiedostoa. Muut lukevat sitä ja tekevät ehdotuksia kansioon `docs/proposals/`.

| Polku | Omistaja |
|---|---|
| `Blender/SunshoreBay/**` (myös `build_sunshore_bay.py`) | **01** |
| `Assets/_Project/Art/World/**` | **01** |
| `Blender/Assets/**` | **02** |
| `Assets/_Project/Art/Environment/**` | **02** |
| `Blender/Characters/**` | **03** |
| `Assets/_Project/Art/Characters/**` | **03** |
| `Assets/_Project/Animation/**` | **03** |
| `Assets/_Project/Scripts/Animation/**` (uusi: animator-ajurit, ragdoll-visuaalit) | **03** |
| `Assets/_Project/Scripts/Fishing/**` | **04** |
| `Assets/_Project/Scripts/Fish/**` | **04** |
| `Assets/_Project/Scripts/Boat/**` | **04** |
| `Assets/_Project/ScriptableObjects/FishSpecies/**` | **04** |
| `Assets/_Project/Prefabs/Fish/**` | **04** |
| `Assets/_Project/Prefabs/Fishing/**` | **04** |
| `Tests/PlayMode/FishingSmokeTests.cs` (+ uudet kalastus- ja venetestit) | **04** |
| `Assets/_Project/Atmosphere/**` | **05** |
| `Assets/_Project/Settings/URP/DefaultVolumeProfile.asset` | **05** |
| `Assets/_Project/Scenes/**` (**kaikki `.unity`-skenet**) | **06** |
| `Assets/_Project/Prefabs/Player/**` | **06** |
| `Assets/_Project/Prefabs/Environment/**` | **06** |
| `Assets/_Project/Scripts/Player/**` | **06** |
| `Assets/_Project/Scripts/Core/**` | **06** |
| `Assets/_Project/Scripts/UI/**` | **06** |
| `Assets/_Project/Settings/InputActions/**` | **06** |
| `Assets/_Project/Settings/URP/*Pipeline*`, `*Renderer*`, `UniversalRenderPipelineGlobalSettings.asset` | **06** |
| `*.asmdef` | **06** |
| `Tests/PlayMode/MovementSmokeTests.cs` | **06** |
| `Packages/**`, `ProjectSettings/**`, `.gitignore`, `.gitattributes` | **06** |
| `Assets/_Project/Sandbox/<alue>/**` | kyseinen alue |

### Yhteiset dokumentit
| Dokumentti | Muokkaaja |
|---|---|
| `CLAUDE.md`, `PROJECT_STRUCTURE.md`, `DESIGN.md`, `README.md` | **06**, ehdotusten perusteella |
| `ART_DIRECTION.md`, `LURELOOM_PRODUCTION_PLAN.md`, `GAME_DESIGN.md` | **vain käyttäjä**, tai sessio hänen nimenomaisella pyynnöstään |
| `docs/workstreams/0X-*.md` | kyseinen alue (oma ohje), 06 rakenteen osalta |
| `docs/proposals/*` | kuka tahansa voi lisätä uusia tiedostoja. Olemassa olevaa ehdotusta muokkaa vain sen kirjoittaja tai omistaja vastatessaan. |

## 5. Riippuvuudet alueiden välillä

```
ART_DIRECTION ──► kaikki

01 World & Map ──(layout, merkkipisteet MK_*, heightmap)──► 06
02 Buildings & Nature ──(mallit Art/Environment)──► 06 (prefabit) ──► 01 (korvaa blockout-proton)
03 Characters & Animation ──(rig, klipit)──► 06 (Player.prefab) ◄── PlayerMotor (06)
04 Fishing & Physics ──(rod/line/fish/boat-koodi)──► 06 (Player.prefab, skenet)
                     ◄──(kalastusanimaatiot)── 03
05 Atmosphere & Horror ──(valot, sumu, volume, VFX prefabit)──► 06 (skene)
                       ◄──(Forgotten Islen layout)── 01
```

Rajapinnat, joista sovitaan ehdotuksilla:
- **Player.prefab** (06): 03 tuo mallin ja animaattorin, 04 tuo vavan ja siiman. Kumpikaan ei muokkaa prefabia itse, vaan toimittaa oman komponenttinsa tai alaprefabinsa ja ohjeen.
- **Pelaajan tila → animaatio** (03 ↔ 04 ↔ 06): animaatioajuri lukee tilaa (`PlayerMotor`, `FishingRod.State`) ja kirjoittaa vain Animatoriin. Pelilogiikka ei riipu animaatioista.
- **Merkkipisteet** (01 → 06): `MK_PlayerSpawn`, `MK_FishingSpot_XX` ja `MK_Zone_*` pidetään nimiltään vakaina.
- **Prototyyppien vaihto** (02 → 01): 02 toimittaa mallin, jonka origo ja mittakaava ovat samat kuin vastaavalla `PROTO_*`-prototyypillä, ja 01 vaihtaa sen mapin skriptiin.

## 6. Työnkulku

### Worktreet (rinnakkaiset sessiot)
Jokainen alue työskentelee omassa kansiossaan omalla haarallaan. Alkuperäinen kansio `C:\Users\kappu\fishing` pysyy `main`-haarassa. Sitä käytetään tarkasteluun ja yhdistämiseen, ei kehitykseen.

```
C:\Users\kappu\fishing                       main (tarkastelu / yhdistäminen)
C:\Users\kappu\lureloom\01-world-map          feature/world-map
C:\Users\kappu\lureloom\02-buildings-nature   feature/buildings-nature
C:\Users\kappu\lureloom\03-characters-anim    feature/characters-animation
C:\Users\kappu\lureloom\04-fishing-physics    feature/fishing-physics
C:\Users\kappu\lureloom\05-atmosphere-horror  feature/atmosphere-horror
C:\Users\kappu\lureloom\06-unity-integration  feature/unity-integration
```

- Worktreet jakavat saman git-historian mutta **eivät committaamattomia tiedostoja**.
- Unity luo jokaiseen worktreehen oman `Library/`-kansion. Ensimmäinen avaus kestää kauan, ja jokainen kopio vie levytilaa. Avaa Unity vain niissä worktreissä, joissa sitä tarvitaan (04, 05, 06, myöhemmin 03).
- Samaa worktreetä ei saa avata kahdessa Unityssä eikä kahdessa Claude-sessiossa yhtä aikaa.

### Yhdistäminen
1. Alue tekee pieniä committeja omaan haaraansa ja pushaa haaran käyttäjän luvalla.
2. Kun kokonaisuus on valmis ja hyväksytty, avataan PR `feature/<alue>` → `main`.
3. **06 Unity Integration** tarkistaa PR:n: testit, `.meta`-tiedostot, ettei omistajuusrajoja ole rikottu ja että toimitukset toimivat yhdessä. Sen jälkeen käyttäjä hyväksyy yhdistämisen.
4. Muut alueet hakevat `main`-haaran omaan haaraansa: `git fetch origin` ja sitten `git merge origin/main`.
5. Yhdistämisjärjestys, kun useita PR:iä on auki: dokumentit ja rakenne ensin, sitten koodi (04, 06), sitten assetit (02, 03), lopuksi skenemuutokset (06).

### Ristiriitojen esto
- Skenet (`*.unity`) ja `Player.prefab` ovat yhden omistajan (06) tiedostoja. Unityn YAML-tiedostojen yhdistäminen on virhealtista.
- `build_sunshore_bay.py` on vain 01:n. 02 ei muokkaa sitä vaan toimittaa prototyyppikorvaajat.
- Uudet `.cs`-tiedostot tehdään omaan kansioon. Jos `Stillwater.Gameplay.asmdef` tarvitsee viittauksen uuteen pakettiin, siitä tehdään ehdotus 06:lle.

### Git LFS (ehdotus 06:lle, ei vielä käytössä)
Nykyinen `.blend` on noin 2 Mt. Kun lopulliset mallit ja tekstuurit tulevat, tarvitaan `.gitattributes`, jossa LFS on käytössä tiedostoille `*.blend`, `*.fbx`, `*.glb`, `*.png`, `*.psd`, `*.wav` sekä Unityn YAML-asetus `*.unity`, `*.prefab` ja `*.asset` → `merge=unityyamlmerge`. Muutos tehdään ennen kuin ensimmäiset isot binäärit commitataan, koska historian muuntaminen jälkikäteen on hankalaa.

## 7. Havaitut riskit
1. **Committaamaton `Blender/`-kansio** on vain kansiossa `C:\Users\kappu\fishing`. Se on commitattava `feature/world-map`-haaraan ennen worktreiden luontia, muuten 01 ei näe sitä omassa worktreessään.
2. **`origin/blender-lake-map`** sisältää toisen mapin generaattorin (`Tools/Blender/generate_map.py`). Se on päällekkäinen Sunshore Bayn kanssa. Käyttäjän pitää päättää, yhdistetäänkö se, arkistoidaanko se vai jätetäänkö se pois. Kunnes päätös on tehty, haaraan ei kosketa.
3. **Unity puuttuu tältä koneelta.** Testejä ei voi ajaa täällä, ja DESIGN.md:n testikomento on Macin polulla.
4. **Player.prefab** on luonteva ristiriitapiste (03, 04 ja 06 kaikki tarvitsevat sitä). Se on ratkaistu yhdellä omistajalla.
5. **Sisäinen nimi Stillwater ja työnimi LURELOOM.** Uudelleennimeäminen koskisi asmdefiä, nimiavaruuksia ja assetteja, joten se tehdään vain erillisellä päätöksellä (06).
6. **Unity Library -kopiot:** 4–6 Unity-worktreetä vie paljon levytilaa ja ensimmäisellä avauksella aikaa.
