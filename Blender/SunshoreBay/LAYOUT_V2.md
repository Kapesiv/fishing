# Sunshore Bay – sijoittelu v2 (ehdotus ja toteutus)

Tila: **odottaa hyväksyntää.** Ei vielä commitattu.

Versiot:
- **v1:** `SunshoreBay_Blockout.blend`, `renders/*.png`, skripti `versions/v1/build_sunshore_bay_v1.py`
- **v2:** `SunshoreBay_Blockout_v2.blend`, `renders/v2/*.png`, skripti `scripts/build_sunshore_bay.py`

Kokonaisuus pysyy 400 × 400 m:n kokoisena. Objektien nimet ja Unity-merkkipisteet (`MK_PlayerSpawn`, `MK_FishingSpot_00…06`, `MK_Zone_*`) säilyvät. Kalastuspaikat siirtyvät tarvittaessa lähimpään yli 1,5 m syvään kohtaan, mutta niiden nimet pysyvät samoina.

## 1. Kalastajakylä
| | v1 | v2 |
|---|---|---|
| Rakenne | talot rivissä suoran raitin varrella | kolme pientä ryhmää aukion ympärillä |
| Aukio | – | **kyläaukio** (r ≈ 9,5 m): kivetys, kaivo, ilmoitustaulu, penkit, lyhtyrengas |
| Raitti | suora | mutkitteleva raitti sekä sivupolut: rinnepolku, satamapolku ja itäpolku |
| Korkeudet | tasainen | loiva yläterassi (+1,4 m) kylän takana, kaltevuus alle 12 % |
| Erikoista | – | **puro ja puusilta** kylän länsilaidalla |

Ryhmät:
- **Satama (länsi):** venevaja, punainen mökki vinossa järveen päin, verkkotelineet, länsilaituri.
- **Aukio:** kauppa päätyineen aukiota kohti ja minttumökki kylki järveen. Puupolku vie aukiolta suoraan päälaiturille.
- **Yläterassi:** sininen ja okra mökki pihoineen ja aitoineen, järvinäkymä.
- **Varasto** on itälaiturin vieressä, ja sen pääty osoittaa laituria kohti.

## 2. Järvi
- Rantaviivassa on 10 poukamaa ja niemeä, muun muassa Pinewood Point luoteessa, satamaniemi kylän itäpuolella ja kaislikkoinen poukama lännessä. Lisäksi rantaviivassa on hienompaa vaihtelua.
- Saaret ovat pitkulaisia ja epäsymmetrisiä, ja niissä on sivulohkoja.
- Avointa vettä jää keskelle noin 150 × 120 m kalastukseen ja veneilyyn.

## 3. Metsä (uusittu: tummempi, realistisempi)
Vanhat puut on poistettu kokonaan ja korvattu uusilla, hieman dark fantasy -henkisillä lajeilla:
- **Gloom Spruce:** korkea ja kapea tumma kuusi, jonka oksakerrokset roikkuvat sakaraisina.
- **Crooked Pine:** vanha mänty, jonka rungon alaosa on paljas ja jonka leveä latvus koostuu neulastasanteista.
- **Ashen Birch:** hoikka ja vaalea koivu, jossa on oliivinvihreä ja yhdessä muunnelmassa meripihkainen lehvästö.
- **Kuolleet ja maassa:** kelot, kaatuneet rungot ja kannot. Lisäksi taimia isojen puiden väleissä.
- **Aluskasvillisuus:** saniaiset, piikikkäät tummat pensaat, kanerva kuivilla kohdilla ja muutama himmeästi hehkuva sieniryhmä kosteassa metsässä.

Sijoittelu:
- Puut arvotaan satunnaisiin kohtiin ilman ruudukkoa, ja jokaisella puulla on oma latvustilansa.
- Puulaji määräytyy paikan mukaan:
  - kuuset kosteisiin ja tiheisiin sisäosiin
  - männyt kuiville rinteille, kallioille ja rannoille, joilla ne kurottuvat veden ylle
  - koivut metsän reunoille, aukeille ja puron varteen
- Reunoilla kasvaa nuorempia ja pienempiä puita, sisäosissa isoja. Puut kallistuvat hieman rinteen suuntaan.
- Metsäaukeat, avoimet näkymäosuudet polkujen varrella ja harvempi rantavyöhyke säilyvät.

**Ei päällekkäisyyksiä:** jokainen objekti varaa paikkansa (puut, kivet, rungot, aluskasvit ja kylän esineet). Tarkistusajo: 0 päällekkäistä objektia ja 0 kaksoiskappaletta.

## 4. Forgotten Isle
- **Muoto:** koukkumainen saari, jossa on päärunko, etelään kaartuva itäkäsi, länsilohko ja suojainen poukama rikkinäiselle laiturille.
- **Korkeuserot:** pohjoisreunalla on kallioharjanne, jonka korkein kohta on noin 12 m. Mökki on omalla terassillaan ja kivikehä omalla tasanteellaan.
- **Maamerkki:** kivikehä ja obeliski. (Lure Tree poistettiin 10.11.2026.)
- **Mysteeri päivälläkin:** tummempi kasvillisuus, tummat kuuset ja kuolleet puut, hehkuvat mökin ikkunat, obeliski ja kivikehän ympärillä leijuvat himmeät valot.
- Kivipolku johtaa laiturilta mökille ja kivikehälle, ja siitä erkanee polku huipulle.

## 4b. Saaret ja luodot
- Pienillä saarilla puut kasvavat ryhminä saaren korkeimmalla kohdalla: männyt, muutama kuusi ja koivu.
- Vesirajaa kiertää kivireunus, ja saarten päällä kasvaa kanervaa, saniaisia ja pensaita.
- Uusina on 4 pientä kallioluotoa (`Skerry_1…4`), joista kahdella kasvaa yksinäinen mänty.

## 4c. Talojen sisätilat
Kaikkiin taloihin pääsee sisään:
- Seinät ovat ontot ja oviaukko on avoin, ovi on auki seinää vasten. Ovelle nousee kaksi porrasta, ja sisällä on lankkulattia, kattopalkit ja lyhty.
- **Mökit:** sänky, pöytä, jakkarat, kamiina, hylly ja matto.
- **Kauppa:** tiski, tavarahyllyt ja vapateline.
- **Venevaja ja varasto:** laatikot, tynnyrit ja työpenkki. Venevajassa on lisäksi takaovi maan puolelle.
- **Hylätty mökki:** kaatunut jakkara, vino pöytä ja hehkuva riimukehä lattiassa.

## 5. Maiseman yleisilme
- Avoimuutta rikkovat maastosta lähtevät muodot: kumpareet, kalliopaljastumat, puro ja kylän terassi. Pelkkiä koristeita ei käytetä.
- Avoimilla alueilla on korkeaa heinää, ja kylän laidoilla kasvaa koivuja.

## Avoimet kysymykset ja seuraavat ehdotukset
- Kylän eteläpuolelle ja järven ja kehäpolun väliin jää yhä melko avointa nurmea. Vaihtoehtoja: lisätään viljelypalsta tai heinäpelto aitoineen, tai metsä tuodaan lähemmäs.
- Forgotten Islen harjanne on paljasta kalliota. Lopullisessa versiossa siihen kannattaa lisätä kalliomuotoja ja sammalta (02 Buildings & Nature).
- Mökit voisi suurentaa 10–15 %, kun lopullinen mökki tehdään.

## Laaduntarkistus (QA)
Generaattorin jälkeen ajetaan automaattinen tarkistus:
```
blender -b Blender/SunshoreBay/SunshoreBay_Blockout_v2.blend --python Blender/SunshoreBay/scripts/qa_check.py
```
Tarkistus etsii seuraavat viat:
- leijuvat tai hautautuneet objektit
- puut vedessä
- esineet poluilla
- tukitut oviaukot
- polut veden päällä tai liian jyrkissä kohdissa (yli noin 37°)
- reiät vedessä ja lammen vuodot
- objektit mapin ulkopuolella
- kaksoisnimet ja tarkat duplikaatit.

Tilanne 10.11.2026: **QA SUMMARY clean**, 0 päällekkäisyyttä ja 0 duplikaattia.

Korjatut bugit:
- Polut pidetään automaattisesti kuivalla maalla.
- Kallion jyrkänteen reunalla kulkenut polku siirrettiin.
- Saaren huippupolku poistettiin, koska huipulla ei ole enää mitään.
- Laiturilta mökille tehtiin ramppi.
- Lammen allas tehtiin tiiviiksi.
- Ilmoitustaulu siirrettiin pois kaupan kuistilta ja reppu pois jättirungon sisältä.
- Aidat, kivet ja tynnyrit väistävät polkuja.
- Kuisteille lisättiin alusta.
- Jyrkät kivet, pinoamattomat laatikot ja epätasaiset laikat karsitaan pois.

## Viimeistely, Phase 1 (10.11.2026)
- **Metsä:**
  - mustikanvarvut (1 500)
  - sammalmatot ja neulaskarike maaston väreissä
  - epätasainen metsänpohja
  - kuusten alimmat oksat noin 3 m korkeudella, jotta metsässä voi kulkea ja kamera näkee
  - tiheämmät reunat: taimet ja pensaat
- **Kylä:** ikkunaluukut ja kukkalaatikot, kasvimaat pihoilla, köysikerät, korit ja laatikot laitureilla sekä kylttien halkeamat ja ruosteiset naulat.
- **Avoimet alueet:** kuivat heinälaikut, paljaan mullan kohdat ja tiheämpi, laikuittainen niittyheinä.
- **Järvi:** lumpeet, kivet matalassa vedessä, ajopuut ja pikkukivirannat. Matala vesi on harmaanvihreää eikä trooppista.
- **Mysteerit:**
  - leiristä järvelle johtavat kiireiset jalanjäljet ja pudonnut pipo
  - sammaleiset tavarat leirissä
  - kivikkoinen ja karu luolan ympäristö
  - metsävene, jonka ympärille kasvillisuus on alkanut levitä
- **Valo:** lämpimämpi ja pehmeämpi aurinko (7°), maltillisempi kontrasti, ympäristön varjostus ja epäsuora valo, jos EEVEE tukee niitä.

## Chunky-tyyli (2026-11-11)
How to Fish -henkinen yksinkertaistus. Ei uutta pientä roinaa mappiin.
- **Talot (`house()`):**
  - seinät 0,28 m ja nurkkapylväät 0,36 m
  - katto korkeampi (`rh` = 0,55 × kapeampi sivu), räystäät 0,85 m ja kattolevy 0,38 m paksu
  - ikkunoissa yksi paksu kehys, ruutujako poistettu
  - isommat ikkunaluukut, kukkalaatikot ja lattialautojen saumaviivat poistettu
  - järeämpi savupiippu ja iso, selkeä kauppakyltti
- **Laiturit (`dock()`):** leveät 0,5 m lankut, paksummat paalut 0,34 m ja pollarit; kannen yläpinta ennallaan.
- **Venevaja:** korkea pääty (`rh=4.3`).
- Majakka kokeiltiin ja poistettiin: ei loogista näin pienellä järvellä.
- **Kamera:** `CAM_Eye_Shop`
- **QA:** clean, 0 duplikaattia, 0 päällekkäisyyttä

## Looginen sijoittelu ja aitous (2026-11-11)
Perusteet: `plan/LAYOUT_RULES.md` (tasosuunnittelu, oikeat järvikalastajakylät, esikuvapelit, suomalainen luonto).
- **Kylä:**
  - `BLD_Sauna`: hirsinen rantasauna noin 9 m vedestä, oma `DOCK_Sauna`, lauteet, kiuas, ikkuna ja halkopino takaseinällä. Sijainti puron suun länsipuolella.
  - `BLD_Smokehouse`: nokinen hirsinen savustamo sataman itäpäässä myötätuulessa, vähintään 16 m varastosta.
  - `STR_Woodshed_*` jokaisen mökin vieressä: lautaseinät ja halkopino, jossa halkojen päät näkyvät.
  - Verkkoteline venevajan vieressä; roikkuvat, läpikuultavat tervatut verkot.
  - Kaksi soutuvenettä vedetty rantaan.
- **Talotekniikka:** `log_walls()` tekee pyöreät hirsikerrokset ja ristikkäiset nurkat, `firewood()` halkopinot.
- **Luonto:**
  - lepät (`TREE_Alder_*`) rantaan ja puron varteen
  - 1,6 m:n rantavyöhyke on havupuuton
  - kaislat ja lumpeet vain suojaisissa lahdissa: `fetch()` mittaa avoveden matkan lounaistuulen suunnasta
  - 14 siirtolohkareryhmää (1 iso, 2–3 keskikokoista ja pieniä), sijoitettu ennen metsää
  - katajat kuiviin metsänreunoihin
  - kivien väri lämmin harmaa graniitti (ei enää lumenvalkoinen)
- **Maamerkit:**
  - `TREE_IsleDeadGiant`: noin 22 m:n hopeakelo Forgotten Islen korkeimmalla kohdalla
  - Groven `TREE_GroveGiant_0` 1,5-kertainen, nousee latvuston yli
- **Pelattavuus:**
  - kalapaikat `MK_FishingSpot_00…11`, joista uusia ovat syvänne (10) ja piilolampi (11)
  - jokaisella kalapaikalla custom property `habitat`, jonka perusteella Unity valitsee kalataulukon
  - uudet aluemerkit `MK_Zone_AncientGrove`, `_Falls`, `_OldCamp` ja `_HiddenPond`
- **QA:** clean, 0 duplikaattia, 0 päällekkäisyyttä. `qa_check.py` ei enää tulkitse rinteeseen upotettua puuta leijuvaksi, jos sen alla on maahan haudattu kivi.
