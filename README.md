# Wine Cellar

Wine Cellar e una piccola applicazione web per censire e monitorare vini acquistati, con particolare attenzione agli acquisti En Primeur che restano per alcuni anni presso produttori o merchant.

L'app usa un frontend HTML/CSS/JavaScript e un backend Python basato sulla libreria standard. I dati sono salvati in SQLite nel file `cellar.db`.

## Funzioni principali

- Inserimento vini con nome, produttore, annata, formato, tipologia, regione, denominazione, merchant, stato e date.
- Gestione stati: ordinato, spedito, in cantina.
- Valute CHF, EUR e USD con conversione verso CHF tramite Frankfurter API / tassi BCE.
- Valore di acquisto e valore attuale unitario aggiornabile manualmente.
- Quote di proprieta per acquisti condivisi, con altri proprietari e percentuali.
- Dettaglio posizione con valori personali e totali.
- Registrazione di bottiglie bevute.
- Registrazione vendite con quantita, prezzo, acquirente e utile/perdita realizzata.
- Punteggi manuali per critici/testate, ad esempio Suckling, Falstaff, Vinous, Wine Advocate.
- Autocomplete locale dei vini gia inseriti e catalogo precaricato di etichette importanti.
- Timeline delle consegne future.
- Statistiche separate per mia quota, posizioni condivise e posizioni totali.
- Filtri in cantina per stato e proprieta, con pannello collassabile.
- Import/export JSON.
- Interfaccia disponibile in italiano e inglese.
- Modalita admin/viewer: chi consulta puo vedere i dati senza modificarli.

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

Il blocco delle modifiche e applicato anche lato server.

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

## Cambi valuta

La valuta di riferimento e CHF. I cambi vengono scaricati da Frankfurter API, basata sui tassi di riferimento BCE, e salvati in cache per 12 ore.

Per forzare l'aggiornamento:

```sh
curl http://localhost:4173/api/rates
```
