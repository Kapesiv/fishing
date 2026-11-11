# LURELOOM – ohjeet Claude Code -sessioille

LURELOOM on 1–4 pelaajan stylized 3D -kalastusseikkailu (Unity 6 + URP + C#, mallit Blenderissä). Päivällä maailma on lämmin ja kutsuva, yöllä salaperäinen ja ajoittain pelottava.
Unity-projektin sisäinen nimi on vielä **Stillwater** (asmdef, input actions, URP-assetit). Älä nimeä niitä uudelleen ilman päätöstä.

## Lue ensin
1. [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md): kansiot, kuusi vastuualuetta ja tiedostojen omistajuus
2. [`ART_DIRECTION.md`](ART_DIRECTION.md): graafinen tyyli, mittakaavat, Blender- ja Unity-standardit
3. Oma ohjeesi: `docs/workstreams/0X-*.md`
4. Taustaksi:
   - [`LURELOOM_PRODUCTION_PLAN.md`](LURELOOM_PRODUCTION_PLAN.md): päätösasiakirja
   - [`DESIGN.md`](DESIGN.md): tekninen arkkitehtuuri ja tila
   - [`GAME_DESIGN.md`](GAME_DESIGN.md): alkuperäinen visio

## Tärkeimmät säännöt
1. **Pysy omalla alueellasi.** Muokkaa vain niitä tiedostoja, jotka `PROJECT_STRUCTURE.md` antaa sinun vastuualueellesi. Jos tarvitset muutoksen toisen alueen tiedostoon, kirjoita ehdotus kansioon `docs/proposals/` (ks. [`docs/proposals/README.md`](docs/proposals/README.md)). Älä muokkaa tiedostoa itse.
2. **Älä poista toimivia järjestelmiä.** Pelaajan liikkuminen (Phase 1) ja kalastus (Phase 2) testeineen säilyvät.
3. **Älä muuta taidesuuntaa itsenäisesti.** ART_DIRECTION.md muuttuu vain käyttäjän hyväksynnällä.
4. **Hahmot ovat ihmismäisiä** (How to Fish -henki, noin 1,75–1,85 m). Ei chibi-hahmoja, isopäisiä maskotteja eikä lelumaisia hahmoja.
5. **Unity-skenejä (`*.unity`) muokkaa vain 06 Unity Integration.** Muut tekevät prefabeja ja käyttävät omaa sandbox-skeneään (`Assets/_Project/Sandbox/<alue>/`).
6. **Säilytä `.meta`-tiedostot.** Siirrä ja nimeä Unity-assetit uudelleen vain Unityn kautta tai yhdessä `.meta`-tiedoston kanssa.
7. **Laatu ennen määrää.** Tee yksi hyväksytty kokonaisuus kerrallaan ja näytä renderöinnit tai testitulokset ennen seuraavaa vaihetta.
8. **Älä committaa tai pushaa ilman käyttäjän hyväksyntää.**

## Git-käytännöt
- Jokaisella alueella on oma haara ja oma worktree-kansio (ks. PROJECT_STRUCTURE.md → Työnkulku).
- `main` on vakaa. Siihen yhdistetään vain hyväksyttyjä ja testattuja muutoksia Pull Requestin kautta, ja 06 Unity Integration tekee yhdistämisen.
- Tee pieniä committeja, joissa on selkeä viesti: `[world-map] Loivenna kylän takarinne`.
- Hae `main` omaan haaraan säännöllisesti: `git fetch origin` ja sitten `git merge origin/main`, mieluummin ennen isoja muutoksia.
- Älä koskaan aja komentoja `git push --force`, `git reset --hard` tai `git clean`, äläkä poista haaroja ilman lupaa.
- Worktreet eivät jaa committaamattomia tiedostoja. Mitä et ole commitannut, näkyy vain omassa kansiossasi.
- Isot binääritiedostot (`.blend`, `.fbx`, tekstuurit): ks. Git LFS -kohta PROJECT_STRUCTURE.md:ssä.

## Testauskäytännöt
- **Unity:** PlayMode-testit ovat kansiossa `Assets/_Project/Tests/PlayMode/` (kalastus ja liikkuminen). Aja ne ennen jokaista PR:ää, joka koskee C#-koodia, prefabeja tai skenejä:
  ```
  Unity -batchmode -nographics -projectPath <worktree> -runTests -testPlatform PlayMode -testResults results.xml -logFile -
  ```
  Unity 6000.0.85f2 ei ole asennettuna jokaisella koneella. Jos testejä ei voi ajaa, kerro se raportissa. Älä väitä testien menneen läpi.
- Testisilmukoissa käytä kulunutta aikaa (`Time.deltaTime`), älä framemäärää (ks. DESIGN.md, Phase 2 -bugi 2).
- **Blender:** generointiskriptien pitää ajautua puhtaasti komennolla `blender -b --python <skripti>`. Liitä raporttiin esikatselurenderöinnit.
- Kerro raportissa aina: mitä tehtiin, miten se testataan, mitä puuttuu ja mikä on seuraava askel.

## Työkalut tällä koneella (Windows)
- Blender 5.0: `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`. BlenderMCP-lisäosa on asennettu, ja sen palvelin käynnistetään Blenderin N-paneelista.
- Unity: ei asennettu tälle koneelle (marraskuu 2026).
