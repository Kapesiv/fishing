# LURELOOM — KOKONAISVALTAINEN PELI- JA 3D-TUOTANTOSUUNNITELMA

## 1. Mikä LURELOOM on?

LURELOOM on kehitteillä oleva 1–4 pelaajan PC-kalastus- ja tutkimisseikkailu, joka rakennetaan Unity 6:lla.

Peli yhdistää kolme tärkeää asiaa:

1. **Hauska, fysiikkapohjainen pelaaminen** — kalastaminen, veneily, kömpelöt liikkeet ja yllättävät tilanteet kavereiden kanssa.
2. **Kaunis ja tutkittava 3D-maailma** — kalastajakyliä, järviä, metsiä, saaria, luolia ja salaisia paikkoja.
3. **Syvä mysteerinen tarina** — maailma näyttää aluksi tavalliselta, mutta vähitellen pelaajille paljastuu, että järvien ja saarien historiaan liittyy jotain paljon suurempaa.

Peli ei ole realistinen kalastussimulaattori. Sen pitää olla hauska, helposti lähestyttävä ja visuaalisesti persoonallinen.

Tunnelma jakautuu suunnilleen näin:
- 50 % rento, hauska ja lämmin
- 50 % salaperäinen, synkkä ja jännittävä

Päivällä pelaajat voivat kalastaa, tutkia ympäristöä ja seikkailla kavereiden kanssa.

Yöllä maailma muuttuu. Sumua voi nousta järvelle, veden alla voi liikkua tuntemattomia olentoja ja syrjäisistä paikoista voi löytyä vihjeitä vanhoista tapahtumista.

Tarina paljastuu vähitellen ympäristön, tutkimisen, hahmojen ja löydettävien esineiden kautta.

## 2. Nykyinen tekninen projekti

GitHub:
https://github.com/Kapesiv/fishing

Unity-projektin aiempi nimi on Stillwater, mutta pelin nykyinen työnimi on LURELOOM.

Käytössä:
- Unity 6 LTS, aiemmin 6000.0.85f2
- Universal Render Pipeline (URP)
- Unity Input System
- C#
- Git ja GitHub

Aiemmin vahvistetut toteutukset:

**Phase 1 — Pelaajan liikkuminen**
- PlayerInputReader
- PlayerMotor
- ThirdPersonCamera
- CharacterController-pohjainen liikkuminen
- Hyppy
- Kameran suuntainen ohjaus
- TestWorld-skene

**Phase 2 — Kalastuksen perusjärjestelmä**
- FishSpeciesConfig
- FishBehaviour
- FishingHook
- FishingLine
- FishingRod
- Ensimmäinen kala, Perch
- Testivesialue

Aiemmin 11 PlayMode-testiä läpäisi onnistuneesti.

Käyttäjä on tämän jälkeen kertonut valmistelulistan valmistuneen. Tarkista reposta, mitä animaatioista, ragdollista, veneilystä, vedestä ja tavaroiden käsittelystä on toteutettu.

Älä oleta ominaisuuksia valmiiksi ilman tarkistusta.

Kaikki olemassa olevat toimivat järjestelmät pitää säilyttää.

## 3. Tärkein tavoite tällä hetkellä

Emme keskity vielä uusien pelimekaniikkojen lisäämiseen.

**Nyt rakennamme LURELOOMille oman visuaalisen identiteetin ja ensimmäisen laadukkaan pelimaailman.**

Käytämme:
- Blenderiä 3D-mallien luomiseen
- Blender Pythonia automatisointiin
- Unityä varsinaisen maailman kokoamiseen
- Claude Codea toteutuksen suunnitteluun ja ohjelmointiin

Tavoitteena ei ole nopeasti generoitu testimaailma.

Tavoitteena on maailma, joka näyttää laadukkaalta, persoonalliselta indiepeliltä.

## 4. Graafinen tyyli

LURELOOMin grafiikka on värikästä, pehmeää ja hieman sarjakuvamaista 3D:tä.

Visuaalinen suunta:
- How to Fish -henkinen ihmismäinen hahmotyyli
- Tyylitelty mutta uskottava ympäristö
- Pehmeät muodot
- Kauniit luonnonvärit
- Värikkäät rakennukset
- Kirkas järvivesi
- Vehreät metsät
- Tyylitellyt kalliot
- Lämmin auringonvalo
- Hieman liioitellut, persoonalliset yksityiskohdat

Maailma ei saa näyttää täysin realistiselta eikä myöskään liian yksinkertaiselta low-poly-testipeliltä.

Tavoitteena on tasapaino uskottavan maailman ja leikkisän visuaalisen tyylin välillä.

Päivän väripaletti:
- Turkoosinsininen vesi
- Syvänvihreät männyt
- Vaaleanvihreä ruoho
- Lämpimänruskea puu
- Punaiset, siniset ja kellertävät rakennukset
- Vaaleat kalliot
- Pehmeä sininen taivas

Yöversiossa:
- Tummansininen ympäristö
- Viileät varjot
- Pehmeä sumu
- Lämpimät lyhdyt
- Hienovaraiset mysteeriset valot

Päivä- ja yöversioiden pitää tuntua samalta maailmalta.

## 5. Pelaajahahmo — erittäin tärkeä

Aiempi ajatus pienestä isopäisestä maskottihahmosta on hylätty.

**Pelaajahahmon pitää olla selvästi ihmismäinen, How to Fish -pelin henkinen.**

Mittasuhteet:
- Noin 1,75–1,85 metriä pitkä
- Normaalin kokoinen pää
- Selkeä ihmisen vartalo
- Normaalit kädet
- Pitkähköt jalat
- Luonnollinen mutta hieman tyylitelty anatomia

Hahmo ei saa näyttää:
- Chibi-hahmolta
- Lelulta
- Pallomaiselta maskotilta
- Minecraft-hahmolta
- Täysin realistiselta ihmiseltä

Hahmon persoonallisuus tulee erityisesti ilmeistä, vaatetuksesta, animaatioista ja fysiikasta.

Ensimmäinen hahmo:
- Nuorehko aikuinen kalastaja
- Rento ulkoilutakki
- Huppari tai paita
- Tavalliset ulkoiluhousut
- Saappaat
- Lippalakki tai pipo
- Pieni reppu

Kasvojen tulee olla yksinkertaiset mutta ilmeikkäät.

Hahmon pitää olla mahdollista muokata myöhemmin eri vaatteilla, väreillä, kampauksilla ja asusteilla.

Tee Blenderissä ensin:
1. Hahmon perusmalli
2. Etunäkymä
3. Sivunäkymä
4. Takanäkymä
5. Yksinkertainen riggaus
6. Unity-tuontitesti

Älä rakenna useita hahmoja ennen ensimmäisen hyväksymistä.

## 6. Hahmojen animaatiot ja fysiikka

LURELOOMin hahmojen tulee tuntua hauskoilta ohjata.

Liikkeet voivat olla hieman kömpelöitä ja liioiteltuja, mutta ohjauksen pitää pysyä tarkkana.

Tarvittavat animaatiot:
- Idle
- Walk
- Run
- Jump
- Fall
- Land
- Swim
- Fishing idle
- Casting
- Reeling
- Carrying
- Boat sitting

Fysiikka:
- Hahmo voi horjahtaa
- Suuri kala voi vetää hahmoa
- Hahmo voi kaatua
- Pelaajat voivat myöhemmin törmäillä toisiinsa
- Hahmo voi pudota veteen
- Ragdoll aktivoituu vain sopivissa tilanteissa

Älä anna ragdollin häiritä tavallista liikkumista.

Animaatioiden pitää toimia nykyisen PlayerMotor-järjestelmän kanssa.

## 7. Ensimmäinen mappi — Sunshore Bay

Rakennamme ensimmäisen yhtenäisen pelialueen nimeltä Sunshore Bay.

Alustava koko noin 400 × 400 metriä.

Alueen keskellä on järvi.

Järven ympärillä sijaitsevat:
- Kalastajakylä
- Metsä
- Kalliot
- Rannat
- Pieniä saaria
- Salaperäinen saari

Maailman pitää olla vapaasti tutkittava.

### A. Sunshore Village

Pelaajan aloituspaikka.

Pieni, persoonallinen kalastajakylä.

Rakennukset:
- Kalastustarvikekauppa
- 3–4 kalastajamökkiä
- Venevaja
- Varastorakennus

Ympäristö:
- Päälaituri
- Pienempiä laitureita
- Puupolkuja
- Kylttejä
- Lyhtyjä
- Tynnyreitä
- Kalastusverkkoja
- Aitoja
- Laatikoita
- Pieniä veneitä

Kylän pitää näyttää asutulta ja uskottavalta.

Rakennukset eivät saa olla identtisiä.

### B. Sunshore Lake

Suuri järvi kylän edessä.

Ominaisuudet:
- Kaunis tyylitelty vesipinta
- Kevyt aallokko
- Pehmeät rannat
- Kiviä ja kaislikkoa
- Kalastuspaikkoja
- Pieniä poukamia
- Tilaa veneilylle
- Muutamia pieniä saaria

Veden pitää näyttää hyvältä sekä rannalta että veneestä.

Veden tekninen toteutus tehdään Unityssä.

### C. Pinewood Forest

Järven ympärillä sijaitseva metsä.

Sisältö:
- Mäntyjä
- Kuusia
- Pensaita
- Kukkia
- Sammaleisia kiviä
- Kallioita
- Polkuja
- Korkeuseroja
- Näköalapaikka

Metsän pitää tuntua luonnolliselta ja kiinnostavalta tutkia.

Älä sijoita puita täysin satunnaisesti.

Suunnittele metsämaisema käsin ohjatun sommittelun ja tarvittaessa proseduraalisen sijoittelun yhdistelmänä.

### D. Forgotten Isle

Pieni salaperäinen saari järven toisella puolella.

Sisältö:
- Hylätty kalastajamökki
- Vanha laituri
- Kallioita
- Puita
- Muutamia erikoisia yksityiskohtia

Saari toimii myöhemmin ensimmäisen mysteerin tapahtumapaikkana.

Älä toteuta vielä varsinaista tarinajärjestelmää.

## 8. Blenderin asset-tuotanto

Blenderissä luodaan uudelleenkäytettäviä 3D-malleja.

Ensimmäinen asset-paketti:

**Rakennukset**
- Kalastustarvikekauppa
- Kalastajamökki
- Venevaja
- Varasto

**Luonto**
- Mänty
- Kuusi
- Pensas
- Kivi
- Kalliomuodostelma
- Ruoho- ja kukkaryhmät

**Rakenteet**
- Modulaarinen laituri
- Portaat
- Aita
- Puusilta
- Kyltti

**Esineet**
- Tynnyri
- Puulaatikko
- Kalastusverkko
- Lyhty
- Poiju
- Kalastusvälineitä

**Veneet**
- Pieni soutuvene
- Yksinkertainen moottorivene myöhempää käyttöä varten

Älä tee kaikkia assetteja heti.

Aloita yhdestä hahmosta, yhdestä mökistä ja yhdestä laiturista.

Niiden perusteella hyväksytään visuaalinen tyyli.

## 9. Blenderin tekniset vaatimukset

Kaikkien mallien pitää olla käyttökelpoisia Unityssä.

Käytä:
- Metristä mittakaavaa
- Selkeitä objektinimiä
- Järkeviä origopisteitä
- Oikein suunnattuja normaaleja
- Sopivia UV-karttoja
- Optimoituja materiaaleja
- Kohtuullisia polygonimääriä
- Modulaarisia rakenteita

Älä tee koko mappia yhtenä mesh-objektina.

Älä myöskään rakenna kaikkea yhdestä valtavasta Blender-tiedostosta.

Säilytä:
- Alkuperäiset .blend-tiedostot
- Mahdolliset Python-generointiskriptit
- Unityyn vietävät assetit
- Esikatselurenderöinnit

Valitse FBX tai glTF/GLB Unity-tuontitestin perusteella.

Varmista erityisesti:
- Mittakaava
- Akselit
- Materiaalit
- Riggaus
- Animaatiot
- Törmäykset

## 10. Unityn ja Blenderin työnjako

Blenderissä tehdään:
- Hahmot
- Rakennukset
- Veneet
- Puut
- Kivet
- Laiturit
- Ympäristöesineet
- Animaatiot

Unityssä tehdään:
- Maasto
- Vesijärjestelmä
- Valaistus
- Pelimaailman kokoaminen
- Törmäykset
- Hahmon liikkuminen
- Kalastus
- Veneily
- Fysiikka
- Interaktiot
- Pelilogiikka

Tavoitteena on tehokas ja ylläpidettävä työnkulku.

## 11. Moninpelivalmius

LURELOOM on tarkoitettu 1–4 pelaajalle.

Moninpeliä ei tarvitse vielä toteuttaa kokonaan.

Huomioi kuitenkin tuleva moninpeli:
- Erota syötteet ja pelilogiikka
- Älä sido kaikkea yhteen paikalliseen pelaajaan
- Suunnittele hahmojen animaatiot uudelleenkäytettäviksi
- Älä tee kalastuksesta riippuvaista käyttöliittymästä
- Pidä pelijärjestelmät modulaarisina

## 12. Kehitysjärjestys

### Vaihe 1 — Ympäristön tarkistus

- Kloonaa GitHub-repo
- Tarkista Unity-projekti
- Tarkista Blender
- Tarkista nykyiset ominaisuudet
- Varmista testien toiminta

### Vaihe 2 — Visuaalisen tyylin lukitseminen

- Päätä väripaletti
- Päätä materiaalien tyyli
- Päätä hahmojen mittasuhteet
- Päätä rakennusten mittakaava
- Luo esikatselukuvat

### Vaihe 3 — Ensimmäinen hahmo

- Mallinna ihmismäinen kalastaja
- Tee hahmolle vaatteet
- Riggaa hahmo
- Testaa Unityssä
- Hyväksytä ulkonäkö

### Vaihe 4 — Ensimmäiset ympäristöassetit

- Kalastajamökki
- Laituri
- Mänty
- Kivi
- Vene

Tee renderöinnit ja Unity-tuontitestit.

### Vaihe 5 — Sunshore Bayn perusrakenne

- Järvi
- Maasto
- Kylän sijainti
- Metsäalue
- Saaret
- Polut

Testaa pelaajan liikkuminen.

### Vaihe 6 — Maailman viimeistely

- Rakennukset
- Kasvillisuus
- Ympäristöesineet
- Valaistus
- Vesiefektit
- Maiseman sommittelu

### Vaihe 7 — Pelattavuuden integrointi

- Pelaajan spawn
- Kalastuspaikat
- Veneily
- Uinti
- Törmäykset
- Interaktiot

### Vaihe 8 — Laadunvarmistus

- Unity-testit
- Virheiden korjaus
- Suorituskyvyn tarkistus
- Visuaalinen hyväksyntä
- DESIGN.md-päivitys

## 13. GitHub ja projektin turvallisuus

Repo:
https://github.com/Kapesiv/fishing

Älä poista nykyisiä toimivia järjestelmiä.

Älä korvaa koko Unity-projektia uudella projektilla.

Älä muuta nykyistä pelilogiikkaa ilman perusteltua tarvetta.

Säilytä Unityn .meta-tiedostot.

Käytä erillisiä committeja ja selkeitä muutoksia.

Varmista Git LFS:n tarve suurille Blender-tiedostoille.

Älä pushaa keskeneräisiä tai testaamattomia muutoksia automaattisesti.

## 14. Tärkeät suunnitteluperiaatteet

1. Laatu ennen määrää.
2. Yhtenäinen taidetyyli.
3. Ihmismäiset, hauskat hahmot.
4. Hyvä liikkumisen ja kalastuksen tuntuma.
5. Kaunis, tutkittava maailma.
6. Hauska fysiikka.
7. Modulaarinen tekninen rakenne.
8. Myöhemmin laajennettava moninpeli.
9. Päivän rentouden ja yön mysteerin yhdistelmä.
10. Oma persoonallinen identiteetti.

## 15. Mitä tehdään ensimmäiseksi?

Aloita tarkistamalla projektin nykyinen tila GitHubista.

Sen jälkeen varmista Blenderin toiminta.

Suunnittele ensimmäinen ihmismäinen LURELOOM-pelaajahahmo, jonka tyyli muistuttaa How to Fishin rentoa, hieman koomista 3D-hahmosuunnittelua mutta jolla on oma tunnistettava ulkoasu.

Tee hahmosta esikatselurenderöinnit.

Älä vielä rakenna koko mappia.

Kun hahmon ulkonäkö on hyväksytty, luo ensimmäinen kalastajamökki ja laituri samalla visuaalisella tyylillä.

Näiden hyväksymisen jälkeen aloitetaan Sunshore Bayn rakentaminen.

**Tärkein ohje: Älä kiirehdi. Haluan, että LURELOOMista tulee oikeasti laadukkaan ja persoonallisen näköinen peli, ei geneerinen Unity-prototyyppi.**
