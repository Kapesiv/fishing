# 06 – Unity Integration

**Haara:** `feature/unity-integration` · **Worktree:** `C:\Users\kappu\lureloom\06-unity-integration`

## Vastuu
- Blender-assetien tuonti (FBX vai glTF -päätös tuontitestin perusteella), skaala, akselit, materiaalit, rigit ja animaatiot
- Unity-prefabit muiden toimituksista (`Prefabs/Environment`, `Prefabs/Player`)
- Skenet: `TestWorld.unity`, tuleva `SunshoreBay.unity` ja niiden kokoaminen
- Törmäykset, suorituskyky, testit ja CI
- Pelaajan ydinkoodi (`Scripts/Player`, `Scripts/Core`, `Scripts/UI`), input actionit, URP-pipeline, Packages ja ProjectSettings
- PR:ien tarkistus ja yhdistäminen `main`-haaraan
- Yhteisten dokumenttien (`CLAUDE.md`, `PROJECT_STRUCTURE.md`, `DESIGN.md`, `README.md`) ylläpito ehdotusten perusteella

## Omat tiedostot
Ks. omistajuustaulukko, PROJECT_STRUCTURE.md, kohta 4 (kaikki rivit "06").

## Ei muokkaa
- Toisten alueiden lähdetiedostoja (Blender-skriptejä, kalastuskoodia, efektejä). Jos integraatio vaatii muutoksen, tee ehdotus omistajalle.
- ART_DIRECTION.md:tä ilman käyttäjän hyväksyntää.

## Säännöt
- Varmista ennen jokaista yhdistämistä: PlayMode-testit menevät läpi, `.meta`-tiedostot ovat mukana, omistajuusrajoja ei ole rikottu eikä skenejä ole muutettu muualla.
- Pidä `Player.prefab` yhtenäisenä: hahmo (03), vapa ja siima (04) sekä liike (06) liitetään yhteen täällä.
- Ehdota Git LFS ja Unity YAML merge (`.gitattributes`) käyttäjälle ennen ensimmäisiä isoja binäärejä.
- Ensimmäiset tehtävät: Unity-tuontitesti 02:n ensimmäisestä mökistä ja laiturista sekä Sunshore Bayn maastoreferenssin tuonti.
