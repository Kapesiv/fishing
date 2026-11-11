# 01 – World & Map

**Haara:** `feature/world-map` · **Worktree:** `C:\Users\kappu\lureloom\01-world-map`

## Vastuu
- Sunshore Bayn maasto, järvi, saaret, rantaviiva ja syvyydet
- Polut, kylän ja metsien aluejako, kiintopisteet (näköalapaikka, niitty, Forgotten Islen layout)
- Maailman mittakaava (400 × 400 m) ja Unity-merkkipisteet `MK_*`
- Mapin generointiskripti `Blender/SunshoreBay/scripts/build_sunshore_bay.py`
- Heightmap tai maastoreferenssi Unityyn (`Assets/_Project/Art/World/`)

## Omat tiedostot
- `Blender/SunshoreBay/**`
- `Assets/_Project/Art/World/**`
- `Assets/_Project/Sandbox/World/**`

## Ei muokkaa
- Hahmoja, kalastuslogiikkaa, Unity-skenejä eikä 02:n asset-skriptejä (`Blender/Assets/**`).
- Lopullisia rakennus- tai puumalleja ei mallinneta täällä. Mapissa käytetään blockout-prototyyppejä (`PROTO_*`), kunnes 02 toimittaa korvaajat.

## Säännöt
- Objektien nimet ja merkkipisteiden nimet (`MK_PlayerSpawn`, `MK_FishingSpot_XX`, `MK_Zone_*`) pysyvät vakaina, koska 06 käyttää niitä.
- Edelliset versiot säilytetään (`Blender/SunshoreBay/versions/`).
- Jokaisen muutoksen jälkeen tehdään yleiskuvat ja pelaajan korkeudelta (1,7 m) otetut renderöinnit.
