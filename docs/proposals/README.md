# Muutosehdotukset

Kun tarvitset muutoksen tiedostoon, jonka omistaa toinen vastuualue (ks. `PROJECT_STRUCTURE.md`), **älä muokkaa tiedostoa**. Luo sen sijaan tähän kansioon uusi tiedosto:

```
docs/proposals/YYYY-MM-DD_<lähettäjä>-to-<omistaja>_<aihe>.md
esim. 2026-11-12_04-to-06_reel-input-action.md
```

Sisältö:
```markdown
# <aihe>
- Lähettäjä: 04 Fishing & Physics
- Omistaja: 06 Unity Integration
- Tiedosto(t): Assets/_Project/Settings/InputActions/StillwaterControls.inputactions
- Tila: avoin | hyväksytty | toteutettu | hylätty

## Miksi
## Ehdotettu muutos (mahdollisimman tarkasti, esim. diff)
## Vaikutus muihin
```

Omistaja päivittää tilan ja toteuttaa muutoksen omassa haarassaan. Jokainen ehdotus on oma tiedostonsa, joten ehdotukset eivät aiheuta merge-ristiriitoja.
