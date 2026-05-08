# Wine Cellar

Wine Cellar e una piccola applicazione web per censire e monitorare vini acquistati, con particolare attenzione agli acquisti En Primeur che restano per alcuni anni presso produttori o merchant.

L'app usa un frontend HTML/CSS/JavaScript e un backend Python basato sulla libreria standard. I dati sono salvati in SQLite nel file `cellar.db`.

## Funzioni principali

- Inserimento vini con nome, produttore, annata, formato, tipologia, regione, denominazione, merchant, stato e date.
- Gestione stati: ordinato, spedito, in cantina.
- Valute CHF, EUR e USD con conversione verso CHF tramite Frankfurter API / tassi BCE.
- Valore di acquisto e valore attuale unitario aggiornabile manualmente.
- Stima AI del valore attuale unitario, generata a richiesta e salvata sulla posizione.
- Note personali su ogni posizione.
- Note AI generate a richiesta con OpenAI, salvate sulla posizione.
- Finestra di degustazione stimata a richiesta con OpenAI, visualizzata come linea temporale.
- Wishlist separata per opportunita d'acquisto, con prezzo obiettivo, priorita e stato; tutte le utenze possono usarla, mentre eliminazione e conversione in ordine restano riservate ad admin.
- Quote di proprieta per acquisti condivisi, con altri proprietari e percentuali.
- Dettaglio posizione con valori personali e totali.
- Registrazione di bottiglie bevute.
- Registrazione vendite con quantita, prezzo, acquirente e utile/perdita realizzata.
- Punteggi manuali per critici/testate, ad esempio Suckling, Falstaff, Vinous, Wine Advocate.
- Autocomplete locale dei vini gia inseriti e catalogo precaricato di etichette importanti.
- Timeline delle consegne future.
- Statistiche separate per mia quota, posizioni condivise e posizioni totali.
- Filtri in cantina per stato e proprieta, con pannello collassabile.
- Import/export JSON, incluse note e wishlist.
- Interfaccia disponibile in italiano e inglese.
- Installazione come PWA su Android/desktop tramite browser.
- Modalita admin/viewer/shared viewer: chi consulta puo vedere i dati senza modificarli; lo shared viewer vede solo le posizioni condivise.

## Avvio locale

Richiede Python 3.

```sh
python server.py --host 127.0.0.1 --port 4173
```

Poi apri:

```text
http://127.0.0.1:4173/
```

Senza password configurate l'app parte automaticamente in modalita admin, utile per sviluppo locale.

## Installazione PWA

Su Android apri l'app via HTTPS, ad esempio `https://bariomwines.duckdns.org/`, poi usa il menu del browser e scegli "Aggiungi a schermata Home" o "Installa app".
La PWA usa una cache leggera per l'interfaccia; dati, login e chiamate API restano serviti dal backend.

## Avvio su server Unix

Lo script `winecellar.sh` avvia l'app in background senza bloccare la console.

```sh
./winecellar.sh start
./winecellar.sh status
./winecellar.sh stop
./winecellar.sh restart
```

Di default ascolta su `0.0.0.0:4173`. Log e PID vengono scritti in:

- `winecellar.log`
- `winecellar.pid`

## Configurazione accessi

Copia il file di esempio:

```sh
cp .env.example .env
```

Modifica `.env`:

```sh
ADMIN_PASSWORD=password-admin-forte
VIEWER_PASSWORD=password-consultazione
SHARED_VIEWER_PASSWORD=password-condivisi
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4-nano
OPENAI_VALUE_MODEL=gpt-5.4-mini
HOST=0.0.0.0
PORT=4173
```

Poi riavvia:

```sh
./winecellar.sh restart
```

Ruoli:

- `admin`: puo creare, modificare, importare, esportare, segnare bottiglie bevute e registrare vendite.
- `viewer`: puo solo consultare cantina, dettaglio, timeline e statistiche.
- `shared_viewer`: puo solo consultare le posizioni condivise, inclusi dettaglio, timeline, vendite e statistiche relative a quelle posizioni.

Il blocco delle modifiche e applicato anche lato server.

## Note AI

Per usare i pulsanti "Genera" nelle Note AI, nella finestra di degustazione e nella stima valore configura `OPENAI_API_KEY` in `.env` e riavvia l'app.
`OPENAI_MODEL` controlla abbinamenti, note e finestra di degustazione; `OPENAI_VALUE_MODEL` controlla la stima valore.
Le chiamate a OpenAI avvengono solo lato server e solo quando un admin le richiede dal dettaglio di una posizione.

## Aggiornamento da Git

Sul server:

```sh
cd /home/administrator/progetti/WineCellar
git pull origin main
./winecellar.sh restart
```

## Database

Il database SQLite e `cellar.db`. Non e versionato da Git.

Per backup rapido puoi usare l'export JSON dall'app oppure copiare `cellar.db` a server fermo.

## Catalogo vini

Il catalogo usato per l'autocomplete e salvato in `data/wine_catalog.json`.
Quando il file cambia, l'app aggiorna automaticamente la tabella `wine_catalog` al successivo avvio.

## Cambi valuta

La valuta di riferimento e CHF. I cambi vengono scaricati da Frankfurter API, basata sui tassi di riferimento BCE, e salvati in cache per 12 ore.

Per forzare l'aggiornamento:

```sh
curl http://localhost:4173/api/rates
```
