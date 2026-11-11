# 05 – Atmosphere & Horror

**Haara:** `feature/atmosphere-horror` · **Worktree:** `C:\Users\kappu\lureloom\05-atmosphere-horror`

## Vastuu
- Päivä- ja yövalaistus sekä niiden välinen siirtymä samassa maailmassa
- Sumu, taivas, post-processing (URP Volume)
- Maagiset efektit, Forgotten Islen mysteerinen ilme (hehku, valot, ääniympäristön suunnittelu)
- Vedenalaiset visuaaliset efektit (sameus, valokeilat, varjot veden alla)
- Lyhtyjen ja muiden valonlähteiden käyttäytyminen yöllä

## Omat tiedostot
- `Assets/_Project/Atmosphere/**` (Scripts/, VFX/, Shaders/, Profiles/, Skyboxes/)
- `Assets/_Project/Settings/URP/DefaultVolumeProfile.asset`
- `Assets/_Project/Sandbox/Atmosphere/**`

## Ei muokkaa
- Skenejä (06), URP-pipeline- tai renderer-assetteja (06), mapin layoutia (01) eikä malleja (02).
- Toimita valaistus ja efektit prefabeina tai profiileina sekä ohje siitä, miten ne lisätään skeneen.

## Säännöt
- **Ei erillistä yö-mappia.** Päivä ja yö ovat sama skene ja sama maailma.
- Päivä on lämmin, värikäs ja kutsuva. Yö on salaperäinen ja ajoittain pelottava. Mysteerinen turkoosi (`#4DF2D9`) säästetään Forgotten Islen ilmiöille.
- Horror rakentuu vihjeistä ja tunnelmasta, ei splatterista.
- Seuraa suorituskykyä: efektien pitää toimia 1–4 pelaajan PC-pelissä.
