# 365_parser_sonicwall

[Italiano](#italiano) · [English](#english)

## Italiano

Scarica l'elenco ufficiale degli endpoint Microsoft 365 e produce due file di testo pronti per l'import in un firewall SonicWall: uno con gli indirizzi IPv4 e uno con i nomi di dominio (FQDN).

Lo script legge il JSON pubblicato da Microsoft (o un file locale nello stesso formato), tiene solo gli IPv4 e gli FQDN compatibili con SonicWall, e scrive i risultati ordinati, una voce per riga.

### Requisiti

- Python 3.9 o successivo
- Nessuna dipendenza esterna

### Configurazione

In cima a `parser.py`:

| Variabile | Ruolo |
| --- | --- |
| `OUTPUT_DIR` | Cartella in cui vengono scritti i file |
| `IPS_FILENAME` | Nome del file con gli indirizzi IPv4 |
| `FQDN_FILENAME` | Nome del file con i nomi di dominio |
| `REQUEST_TIMEOUT_SECONDS` | Secondi massimi di attesa per il download |

La cartella di output viene creata se non esiste. Se l'estrazione non produce indirizzi IP oppure FQDN, lo script si ferma e non sovrascrive i file già presenti.

### Utilizzo

Scarica l'elenco worldwide e scrivi i file nella cartella configurata:

```bash
python3 parser.py https://endpoints.office.com/endpoints/worldwide
```

Oppure elabora un JSON già salvato in locale:

```bash
python3 parser.py test.json
```

Senza argomenti, lo script usa `test.json` nella stessa cartella di `parser.py`, se il file è presente.

### Pubblicazione per i DEAG SonicWall

Se lo script gira su un web server e pubblichi `OUTPUT_DIR`, puoi indicare l'URL HTTPS di ciascun file direttamente in un Dynamic External Address Group (DEAG). Il firewall scarica l'elenco e crea gli oggetti di indirizzo.

In SonicOS 7.1 il percorso è **OBJECT | Match Objects > Dynamic Group**. Per il file degli IPv4 lascia disattivato **FQDN**; per il file dei domini attivalo. Il campo **URL Name** deve iniziare con `https://`. I passaggi sono descritti in [Adding Dynamic External Objects](https://www.sonicwall.com/support/technical-documentation/docs/sonicos-7-1-objects/Content/Match_Objects/Dynamic_Group/adding-object.htm).

Con i nomi predefiniti, se la cartella è pubblicata sotto `https://esempio.it/dwn/`:

- `https://esempio.it/dwn/snwl365.txt`
- `https://esempio.it/dwn/snwl365-fqdn.txt`

### Cosa viene escluso

- Indirizzi IPv6 e qualsiasi valore che non sia un IPv4 valido, con o senza notazione CIDR
- Nomi che non sono un FQDN, compresi schemi, percorsi e spazi
- Wildcard parziali o nel mezzo del nome, come `*cdn.onenote.net` o `autodiscover.*.onmicrosoft.com`

Restano validi gli IPv4 con o senza notazione CIDR e i domini che iniziano con `*.`, come `*.microsoft.com`.

## English

Downloads the official Microsoft 365 endpoint list and writes two text files ready to import into a SonicWall firewall: one with IPv4 addresses and one with domain names (FQDNs).

The script reads the JSON published by Microsoft, or a local file in the same format, keeps only the IPv4 addresses and FQDNs that SonicWall can use, and writes the results sorted, one entry per line.

### Requirements

- Python 3.9 or later
- No third-party dependencies

### Configuration

At the top of `parser.py`:

| Variable | Purpose |
| --- | --- |
| `OUTPUT_DIR` | Directory where the files are written |
| `IPS_FILENAME` | Name of the IPv4 address file |
| `FQDN_FILENAME` | Name of the domain-name file |
| `REQUEST_TIMEOUT_SECONDS` | Maximum seconds to wait for the download |

The output directory is created if it does not exist. If extraction yields no IP addresses or no FQDNs, the script stops and leaves any existing output files unchanged.

### Usage

Download the worldwide list and write the files to the configured directory:

```bash
python3 parser.py https://endpoints.office.com/endpoints/worldwide
```

Or process a JSON file that is already saved locally:

```bash
python3 parser.py test.json
```

With no arguments, the script uses `test.json` in the same directory as `parser.py` when that file is present.

### Publishing for SonicWall DEAGs

If the script runs on a web server and you publish `OUTPUT_DIR`, you can use the HTTPS URL of each file directly as a Dynamic External Address Group (DEAG). The firewall downloads the list and creates the address objects.

In SonicOS 7.1, go to **OBJECT | Match Objects > Dynamic Group**. Leave **FQDN** disabled for the IPv4 file, and enable it for the domain file. **URL Name** must start with `https://`. The steps are described in [Adding Dynamic External Objects](https://www.sonicwall.com/support/technical-documentation/docs/sonicos-7-1-objects/Content/Match_Objects/Dynamic_Group/adding-object.htm).

With the default file names, if the directory is published at `https://example.com/dwn/`:

- `https://example.com/dwn/snwl365.txt`
- `https://example.com/dwn/snwl365-fqdn.txt`

### What is excluded

- IPv6 addresses and any value that is not a valid IPv4 address, with or without CIDR notation
- Names that are not an FQDN, including schemes, paths, and spaces
- Partial wildcards or wildcards in the middle of a name, such as `*cdn.onenote.net` or `autodiscover.*.onmicrosoft.com`

Valid entries are IPv4 addresses with or without CIDR notation, and domains that start with `*.`, such as `*.microsoft.com`.
