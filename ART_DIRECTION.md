# LURELOOM – Art Direction

Kaikki sessiot noudattavat tätä tiedostoa. Muutokset tehdään vain käyttäjän hyväksynnällä.
Lähde: `LURELOOM_PRODUCTION_PLAN.md`, luvut 4–9.

## 1. Pelin tunne
- Hauska kalastusseikkailu 1–4 pelaajalle.
- Stylized 3D: kaunis, puoleensavetävä ja hieman maaginen maailma.
- Tunnelma on noin **50 % rento, lämmin ja hauska** ja **50 % salaperäinen, synkkä ja jännittävä**.
- **Päivällä** maailma on lämmin, värikäs ja kutsuva.
- **Yöllä** sama maailma muuttuu salaperäiseksi ja ajoittain pelottavaksi: sumua, outoja valoja, liikettä veden alla.
- Horror paljastuu vähitellen ympäristön, löydösten ja pienten yksityiskohtien kautta. Siihen ei kuulu splatteria eikä jatkuvia jump scareja.
- Päivä ja yö ovat **samaa maailmaa**. Erillistä yö-mappia ei tehdä.

## 2. Graafinen tyyli
- Pehmeät, hieman sarjakuvamaiset muodot ja hieman liioitellut, persoonalliset yksityiskohdat.
- Tyylitelty mutta uskottava maailma. Se ei ole fotorealistinen eikä liian yksinkertainen low-poly-testipeli.
- Värikkäät rakennukset, kirkas järvivesi, vehreät metsät, tyylitellyt kalliot ja lämmin auringonvalo.
- Esikuvana hahmoissa ja huumorissa on How to Fish. Silti LURELOOMilla on oltava oma tunnistettava ilmeensä.

## 2b. Kasvillisuus (päätetty 10.11.2026)
- Puusto on tyyliteltyä ja hieman **dark fantasy** -henkistä: tummat sinivihreät kuuset, joiden oksakerrokset roikkuvat sakaraisina, vanhat männyt, joiden latvus on leveä, ja vaaleat koivut, joiden lehvästö on oliivinvihreää tai meripihkaista.
- Värit: kuusi `#1D3A33` / `#26473B`, mänty `#2F4E36`, koivun lehdet `#7F844A` / `#A47A3A`, ruoho hillitty `#7FA859`.
- Sijoittelu on luonnollista: puulaji riippuu maastosta, reunat ovat nuorempia, ja metsässä on aukeita. Objektit eivät saa mennä päällekkäin.
- Kirkas ja lämmin tunnelma syntyy kylästä, vedestä ja valosta. Metsä tuo mystiikkaa myös päiväsaikaan.

## 3. Hahmot
- **Ihmismäisiä**: noin 1,75–1,85 m, normaalikokoinen pää, selkeä ihmisen vartalo, normaalit kädet ja pitkähköt jalat.
- **Ei** chibi-hahmoja, leluja, pallomaisia maskotteja, Minecraft-hahmoja eikä täysin realistisia ihmisiä.
- Persoonallisuus syntyy ilmeistä, vaatteista, animaatioista ja fysiikasta. Liikkeet saavat olla hieman kömpelöitä ja liioiteltuja, mutta ohjauksen pitää pysyä tarkkana.
- Ensimmäinen hahmo on nuorehko aikuinen kalastaja: rento ulkoilutakki, huppari tai paita, ulkoiluhousut, saappaat, lippis tai pipo ja pieni reppu.
- Vaatteita, värejä, kampauksia ja asusteita pitää voida vaihtaa myöhemmin (modulaarinen rakenne).

## 4. Väripaletti
**Päivä**

| Kohde | Sävy | sRGB noin |
|---|---|---|
| Järvivesi | turkoosinsininen | `#33A8BD` |
| Männyt, kuuset | syvänvihreä | `#337038` / `#1F573B` |
| Ruoho | vaaleanvihreä | `#94C759` |
| Puu (laiturit, rungot) | lämmin ruskea | `#946640` |
| Rakennukset | punainen / sininen / keltainen / minttu / okra | `#BD3326` `#5280BD` `#F5CC5C` `#94CCAD` `#E0A84D` |
| Kalliot | vaalea harmaa | `#B3B0A8` |
| Taivas | pehmeä sininen | `#9ECCFA` |
| Hiekka | lämmin vaalea | `#E6D19E` |

**Yö**: tummansininen ympäristö, viileät varjot, pehmeä sumu, lämpimät lyhdyt (`#FFC26B`) ja hienovaraiset mysteeriset valot (turkoosi `#4DF2D9`, käytetään säästeliäästi; tunnusväri Forgotten Islen ilmiöille).

## 5. Mittakaavat (metriä, 1 yksikkö = 1 m)
| Asia | Mitta |
|---|---|
| Pelaaja | 1,75–1,85 m, silmät noin 1,7 m |
| Ovi | 2,1 m korkea (vaja tai varasto 3 m) |
| Kerroskorkeus / seinä | 2,7–3,6 m, sokkeli noin 0,45 m |
| Mökin pohja | noin 6–8 × 5,5–7 m (saattaa kasvaa 10–15 % hyväksynnän jälkeen) |
| Laituri | 2,4–2,6 m leveä, kansi noin 1,0 m vedenpinnan yläpuolella |
| Soutuvene | noin 4 × 1,5 m |
| Mänty, kuusi | 9–13 m |
| Pelialue | Sunshore Bay 400 × 400 m, järven pinta y = 0 (Unity) / z = 0 (Blender) |

## 6. Mallinnusperiaatteet
- Metrinen mittakaava, selkeät objektinimet ja järkevät origopisteet (rakennus: pohjan keskellä maan tasolla; puu: rungon juuressa).
- Normaalit oikein, UV:t käyttökelpoiset ja polygonimäärät kohtuulliset.
- Modulaariset rakenteet: laituripalat, aidat ja seinäelementit.
- Mappia ei tehdä yhtenä meshinä eikä kaikkea rakenneta yhteen valtavaan .blend-tiedostoon.
- Säilytä: alkuperäiset .blend-tiedostot, generointiskriptit, Unityyn viedyt tiedostot ja esikatselurenderöinnit.
- Materiaalit: vähän ja yksinkertaisia, mieluiten väripinnat tai pieni paletti-/gradienttitekstuuri. Ei raskaita PBR-tekstuureja.

### Nimeäminen
| Etuliite | Käyttö |
|---|---|
| `BLD_` | rakennukset |
| `DOCK_` | laiturit |
| `STR_` | muut rakenteet |
| `TREE_` `BUSH_` `ROCK_` `REEDS_` `FLOWERS_` | luonto |
| `PROP_` | esineet |
| `BOAT_` | veneet |
| `CHR_` | hahmot |
| `ANIM_` | animaatiot |
| `MK_` | Unity-merkkipisteet (spawn, kalastuspaikat, alueet) |
| `REF_` | apu-/mittakaavaobjektit, joita ei viedä peliin |
| `M_` | materiaalit |
| `P_` / `PROTO_` | prototyyppimeshit |

Unity-prefabit nimetään samoin ilman Blenderin etuliitteen muutoksia (esim. `BLD_Cottage_Red.prefab`).

## 7. Blender ↔ Unity -standardit
- Blender: Z ylös ja −Y eteen. Unity: Y ylös. FBX-viennissä käytä *Apply Transform* -asetusta tai testattua akseliasetusta. Lopullinen formaatti (FBX vai glTF) päätetään 06 Unity Integrationin tuontitestin perusteella.
- Skaala 1,0 kummassakin päässä, eikä objekteihin jätetä applyamattomia skaalauksia.
- Törmäykset: yksinkertaiset `UCX_`-meshit tai Unityn primitiivit. Renderöintimeshiä ei käytetä törmäyksiin, paitsi maastossa.
- Animaatiot: yksi Unityyn sopiva rig kaikille ihmishahmoille (Humanoid-yhteensopiva), ja klipit nimetään `ANIM_<Hahmo>_<Toiminto>`.
- Maaston lopullinen toteutus on Unity Terrain tai mesh. Blender-mapin maasto on referenssi ja heightmapin lähde.

## 8. Mitä ei tehdä
- Ei fotorealismia, ei maksullisia assetteja, ei erillistä yö-mappia eikä chibi-hahmoja.
- Ei suunnan muuttamista itsenäisesti. Jos jokin ei toimi, tee ehdotus kansioon `docs/proposals/`.
