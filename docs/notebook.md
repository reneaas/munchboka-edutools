# Notebook med Python i nettleseren

Munchboka Notebook er en statisk nettside med JupyterLite 0.8.3 og
Pyodide-kjernen 0.8.6. Elevene kan åpne lærerens oppgaver, laste opp `.ipynb`,
redigere tekst og kode, kjøre Python og laste ned arbeidet som en vanlig
Jupyter-notebook. Det trengs ingen Python-server eller elevkonto.

## Installering og selvstendig nettside

Notebook-byggingen krever Python 3.10 eller nyere. Installer i samme Python-miljø
som brukes til bokbyggingen:

```bash
pip install "munchboka-edutools[notebook]"
muncho notebook build --output _build/notebook
python -m http.server 8000 --directory _build/notebook
```

Åpne `http://localhost:8000`. Standardbyggingen inkluderer tre oppgaver:
grunnleggende Python, funksjonsgrafer med NumPy/Matplotlib og derivasjon med SymPy.
Bruk en egen mappe for oppgavene og tilhørende data:

```bash
muncho notebook build --contents oppgaver --output _build/notebook --title "R1 · Notebook"
```

Alle synlige filer i oppgavemappen publiseres. Behold relative mapper for CSV-filer,
bilder og Python-moduler. Notebooks må bruke format 4 og Python. Byggingen validerer
notebook-formatet, men kjører ikke kode. Symbolske lenker avvises.

Hele utdatamappen kan publiseres på en statisk HTTPS-webserver, også under en
undermappe. `file://` støttes ikke. Ved nytt bygg erstattes bare en utdatamappe som
allerede er merket som en Munchboka-notebook. En mislykket bygging beholder forrige
nettside. Uendrede bygg gjenbrukes.

## Sphinx og Jupyter Book

Utvidelsen inngår i `munchboka_edutools`, og kan også aktiveres alene som
`munchboka_edutools.directives.notebook`. Notebook-avhengighetene kreves først når
en HTML-bok faktisk bruker direktivet. Det bygges én notebook-nettside per bok.

````markdown
```{notebook} oppgaver/derivasjon.ipynb
:title: Utforsk den deriverte
:button-text: Åpne notebook
```
````

Standardvisningen er en lenke som åpner oppgaven i en ny fane. For innbygging:

````markdown
```{notebook} oppgaver/funksjoner.ipynb
:title: Utforsk funksjoner
:embed:
:height: 720px
:files: oppgaver/data/maalinger.csv
```
````

Stier tolkes relativt til siden der direktivet står. En innledende `/` betyr
bokas kildemappe. Alle filer må ligge innenfor kildemappen. `files` kan inneholde
flere filstier, én per linje; mappestrukturen bevares i notebook-miljøet. En fil
ved siden av notebooken åpnes dermed i Python med sitt relative navn.

Direktivets argument er valgfritt. Uten et argument vises en blank notebook
(én tom kodecelle) — nyttig for fri utforskning uten å måtte lage en
`.ipynb`-fil på forhånd:

````markdown
```{notebook}
:title: Skriv egen Python-kode
:fullscreen:
```
````

### En egen side i `_toc.yml` som er notebooken

Å legge en `.ipynb`-fil direkte i `_toc.yml` bruker Jupyter Book/MyST-NB sin
vanlige (statiske) notebook-rendring, ikke denne Pyodide-appen. Lag i stedet en
`.md`-side der direktivet er hele innholdet, med `:fullscreen:` i stedet for
`:embed:`/`:height:`:

````markdown
```{notebook} oppgaver/derivasjon.ipynb
:title: Utforsk den deriverte
:fullscreen:
```
````

`:fullscreen:` slår på embedding og lar editoren fylle det meste av
vindushøyden i stedet for en fast pikselhøyde, slik at siden i praksis blir
notebooken. Legg den `.md`-filen i `_toc.yml` som en vanlig side/kapittel.

Tittel for hele nettsiden kan settes i Jupyter Books `_config.yml`:

```yaml
sphinx:
  extra_extensions:
    - munchboka_edutools
  config:
    munchboka_notebook_title: "Matematikk R1 · Notebook"
```

HTML- og dirhtml-bygg støttes. Tekst/LaTeX viser oppgavenavn og filsti. Nettleserutskrift
viser lenken og skjuler den innebygde editoren.

## Elevens arbeid

- **Åpne fil** lager en egen kopi av en lokal `.ipynb` (maks. 25 MB).
- **Last ned notebook** eksporterer den åpne notebooken, inkludert resultater.
- **Kjør celle** og **Kjør alle** kjører kode. Åpning av en fil kjører aldri cellene.
- **Start Python på nytt** tømmer variabler, men beholder tekst, kode og resultater.
- **Åpne originaloppgaven** lager en ny kopi uten å overskrive elevens arbeid.
- **Fortsett i nettleseren** åpner forrige arbeidsområde. Filoversikten inne i
  editoren gir tilgang til tidligere notebooks og opplastede datafiler.

JupyterLite lagrer automatisk i nettleseren. Dette er ikke det samme som en fil i
Nedlastinger. Elevene bør laste ned arbeidet før de lukker, bytter maskin eller leverer.
Private nettleservinduer og sletting av nettleserdata kan fjerne lagrede oppgaver.
Python-variabler overlever ikke en omlasting; kjør cellene på nytt.

Oppgavestier inneholder en innholdshash. Når lærerens oppgaver eller data endres,
får de nye stier, slik at tidligere elevarbeid blir liggende. Gamle versjoner
kan finnes i editorens filoversikt. Lagringen følger nettsidens adresse; flytting
av nettsiden flytter ikke automatisk nettleserdataene.

## Språk, pakker og begrensninger

Startside, verktøylinje og sentrale redigeringskommandoer er på Bokmål.
Oversettelser vedlikeholdes i `notebook/assets/nb_NO.json`. Avanserte Jupyter-menyer
kan fortsatt ha engelske tekster. Python-feilmeldinger beholdes på originalspråket.

Python og pakker lastes fra CDN ved behov. Første oppstart krever internett og kan
ta tid. Dette er ikke en ferdig offline-distribusjon. Koden kjøres lokalt, men
elevens egen kode kan gjøre nettverkskall. Notebook-filer lastes ikke opp til en
Python-server gjennom den vanlige arbeidsflyten.

NumPy, Matplotlib og SymPy demonstreres i eksempeloppgavene. Andre pakker må
være kompatible med Pyodide; installasjon på byggemaskinen gjør dem ikke
tilgjengelige i nettleseren. `plotmath`, `signchart`, widgets og notebooks som
bruker operativsystemfunksjoner trenger særskilt testing. Opplastede notebooks
får ikke automatisk tillit til aktive HTML/JavaScript-resultater.

Python kjører i en Web Worker. Start Python på nytt hvis en uendelig løkke ikke
kan avbrytes. Vanlig avbrytelse avhenger av nettleserens støtte og HTTP-headere.
Ikke sett en restriktiv iframe-sandbox uten å teste Web Workers, lagring og nedlasting.

## Utvikling og tester

```bash
pip install -e ".[dev,notebook]"
pytest -q tests/test_notebook.py
muncho notebook build --output /tmp/munch-notebook-test
# Med Playwright installert og Chromium tilgjengelig:
node tests/notebook_browser.cjs /tmp/munch-notebook-test
```

Nettlesertesten krever tilgang til Pyodide-CDN og tester ekte Python-kjøring,
filimport/eksport, gjenåpning, restart og eksempeloppgavene. Ingen genererte
JupyterLite-bundler sjekkes inn i Git.
