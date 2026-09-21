# Notebook med Python

Elevene kan bruke en notebook med norsk grensesnitt og Python direkte i nettleseren.
De kan åpne ferdige `.ipynb`-oppgaver, redigere tekst og kode og laste ned arbeidet.

Installer den valgfrie funksjonen i bokas byggemiljø:

```bash
pip install "munchboka-edutools[notebook]"
```

Legg en `.ipynb`-fil ved siden av kapitlet og bruk:

````markdown
```{notebook} oppgave.ipynb
:title: Utforsk med Python
:button-text: Åpne notebook
```
````

Legg til `:embed:` og `:height: 720px` for å vise editoren i selve siden.
Bruk `:files:` med én filsti per linje for tilhørende CSV-filer og andre data.

Dropp filargumentet helt for å bare vise en blank notebook (én tom kodecelle),
uten å måtte lage en `.ipynb`-fil først:

````markdown
```{notebook}
:title: Skriv egen Python-kode
:fullscreen:
```
````

## En egen side som *er* notebooken

Å legge en `.ipynb`-fil direkte i `_toc.yml` fungerer ikke som forventet: Jupyter
Book/MyST-NB tolker den da som en vanlig notebook-side (statisk, uten Python i
nettleseren), ikke som denne JupyterLite/Pyodide-appen. Lag i stedet en egen
`.md`-side der `{notebook}`-direktivet er praktisk talt hele innholdet, og legg
den `.md`-filen i `_toc.yml` som en vanlig side:

````markdown
# Notebook

```{notebook} oppgave.ipynb
:title: Utforsk med Python
:fullscreen:
```
````

`:fullscreen:` slår automatisk på `:embed:` og lar editoren fylle det meste av
vindushøyden (CSS med `vh`, siden `:height:` ikke kan settes i `vh`), slik at
siden i praksis oppleves som notebooken selv. En liten lenke for å åpne
notebooken i eget vindu/fane vises fortsatt øverst. Sett `:height:` i tillegg
til `:fullscreen:` for å overstyre med en fast pikselhøyde i stedet.

En selvstendig nettside med tre eksempeloppgaver bygges slik:

```bash
muncho notebook build --output _build/notebook
python -m http.server 8000 --directory _build/notebook
```

Åpne `http://localhost:8000`. Python lastes ved behov. Arbeidet lagres i
nettleseren; **Last ned notebook** gir eleven en `.ipynb`-fil som kan leveres
eller åpnes i vanlig Jupyter. Notebooken krever internett ved første oppstart.



:::{notebook} notebook_test.ipynb
---
embed: true
height: 800px
---
:::