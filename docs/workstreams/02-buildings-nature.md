# 02 – Buildings & Nature

**Haara:** `feature/buildings-nature` · **Worktree:** `C:\Users\kappu\lureloom\02-buildings-nature`

## Vastuu
- Rakennukset: kalastustarvikekauppa, kalastajamökit, venevaja, varasto, hylätty mökki
- Laiturit (modulaariset), portaat, aidat, puusilta, kyltit
- Luonto: mänty, kuusi, pensas, kivet, kalliomuodostelmat, ruoho- ja kukkaryhmät, kaislat
- Esineet: tynnyri, laatikko, verkko, lyhty, poiju, kalastusvälineet
- Veneiden visuaaliset mallit (soutuvene, myöhemmin moottorivene). Veneen fysiikka kuuluu 04:lle.
- Omat modulaariset generointiskriptit ja esikatselurenderöinnit

## Omat tiedostot
- `Blender/Assets/**` (yksi .blend per asset tai asset-perhe, `scripts/`, `renders/`)
- `Assets/_Project/Art/Environment/**` (viedyt mallit ja materiaalit)
- `Assets/_Project/Sandbox/Environment/**`

## Ei muokkaa
- `Blender/SunshoreBay/**`, eli ei myöskään `build_sunshore_bay.py`. Kun malli on valmis, tee 01:lle ehdotus prototyypin vaihdosta.
- Prefabeja kansiossa `Prefabs/Environment` (06) eikä skenejä.

## Säännöt
- Aloita yhdestä mökistä ja yhdestä laiturista, ja hyväksytä tyyli ennen muita (tuotantosuunnitelma, luku 8).
- Mittakaavat, origot ja nimet tulevat ART_DIRECTION.md:stä. Uuden mallin origon ja koon pitää vastata blockoutin `PROTO_*`-prototyyppiä, jotta vaihto mappiin onnistuu.
- Rakennukset eivät saa olla identtisiä: modulaariset osat, mutta jokaisella oma variaationsa.
