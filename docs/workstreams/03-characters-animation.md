# 03 – Characters & Animation

**Haara:** `feature/characters-animation` · **Worktree:** `C:\Users\kappu\lureloom\03-characters-anim`

## Vastuu
- Pelaajahahmot: ensin yksi nuorehko aikuinen kalastaja
- Blender-mallinnus, vaatteet (modulaariset), riggaus
- Animaatiot: idle, walk, run, jump, fall, land, swim, fishing idle, casting, reeling, carrying, boat sitting
- Ragdollin visuaalinen puoli: luut, painot ja nivelrajat Unityyn
- Animaatioajuri, joka lukee pelaajan tilaa ja kirjoittaa Animatoriin (`Scripts/Animation/`)

## Omat tiedostot
- `Blender/Characters/**`
- `Assets/_Project/Art/Characters/**`, `Assets/_Project/Animation/**`
- `Assets/_Project/Scripts/Animation/**`
- `Assets/_Project/Sandbox/Characters/**`

## Ei muokkaa
- `PlayerMotor`, `PlayerInputReader`, `ThirdPersonCamera` eikä `Player.prefab` (06). Toimita hahmo, animaattori ja ohje, ja tee kytkennästä ehdotus 06:lle.
- Kalastuslogiikkaa (04).

## Säännöt
- **Ihmismäinen, How to Fish -henkinen**, noin 1,75–1,85 m, normaalikokoinen pää. Ei chibi-hahmoja eikä maskotteja.
- Tee ensin: perusmalli, etu-, sivu- ja takarenderöinnit, sitten käyttäjän hyväksyntä, sitten yksinkertainen rig ja Unity-tuontitesti. Älä tee useita hahmoja ennen kuin ensimmäinen on hyväksytty.
- Ragdoll ei saa häiritä tavallista liikkumista.
- Animaatiot tehdään uudelleenkäytettäviksi (moninpeli): ei kovakoodattuja viittauksia paikalliseen pelaajaan.
