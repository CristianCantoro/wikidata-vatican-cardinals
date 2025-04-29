Comparing Wikidata and Vatican Official Data about Cardinals
------------------------------------------------------------

This project contains:
  * A list of Cardinals obtained from Wikidata with a [SPARQL query](https://query.wikidata.org/): `wikidata_cardinals.csv`
  * A list of Cardinals obtained by scraping the [College of Cardinals Dashboard](https://press.vatican.va/content/salastampa/en/documentation/cardinali---statistiche/dashboard-collegio-cardinalizio.html) (page 2): `vatican_cardinals.csv`
  * A script to compare the two lists: `compare_cardinal_lists.py`

Both lists contain 252 names and most differences have been solved (see [Differences][https://github.com/CristianCantoro/wikidata-vatican-cardinals?tab=readme-ov-file#differences] below).

## Script Usage

```bash
$ ./compare_cardinal_lists.py -h
usage: compare_cardinal_lists.py [-h] [--output-dir OUTPUT_DIR] <wikidata> <vatican>

positional arguments:
  <wikidata>            Wikidata data.
  <vatican>             Vatican data.

options:
  -h, --help            show this help message and exit
  --output-dir OUTPUT_DIR
                        Output directory [default: output].
```

The script produces up to 5 files:
  * `different_birthdate_wikidata_cardinals.csv`, containing the pairs of cardinals with a different birth date.
  * `different_cardinal_start_wikidata_cardinals.csv`, containing the pairs of cardinals with a different starting date for their cardinalitial tenure.
  * `fuzzymatch_wikidata_cardinals.csv`, containing a list of the names that were fuzzy matched.
  * `missing_vatican_cardinals.csv`, containing the names that appeaer in the Wikidata list, but are missing in the Vatican list.
  * `missing_wikidata_cardinals12.csv`, containing the names that appeaer in the Vatican list, but are missing in the Wikidata list.


## Wikidata Query

This is the query that produces `wikidata_cardinals.csv`.

It deduplicate results for people that have held multiple cardinal roles. It display the earliest time the person became a cardinal. It considers all the subclasses of cardinal recursively (so also subclasses of `cardinal-deacon`, `cardinal-priest` and `cardinal-bishop`).

```sparql
SELECT DISTINCT ?cardinal ?cardinalLabel ?cardinalTypeSampleLabel ?birthDate ?birthPlaceLabel (?earliestCardinalStartTime AS ?cardinalStartTime) ?bishopStartTime ?priestStartTime WHERE {

  # Subquery: Precompute earliest cardinalStartTime per cardinal
  {
    SELECT ?cardinal (MIN(?cardinalStartTime) AS ?earliestCardinalStartTime) (SAMPLE(?cardinalType) AS ?cardinalTypeSample) WHERE {
      ?cardinal wdt:P31 wd:Q5;
                p:P39 ?cardinalPosition.
      ?cardinalPosition ps:P39 ?cardinalType.
      OPTIONAL { ?cardinalPosition pq:P580 ?cardinalStartTime. }

      # Only cardinal types (dynamic)
      ?cardinalType wdt:P279* wd:Q45722.
    }
    GROUP BY ?cardinal
  }

  # Main query
  ?cardinal wdt:P31 wd:Q5;
            wdt:P569 ?birthDate;
            p:P39 ?cardinalPosition.

  ?cardinalPosition ps:P39 ?cardinalType.
  OPTIONAL { ?cardinalPosition pq:P580 ?cardinalStartTime. }

  # Only cardinal types (dynamic)
  ?cardinalType wdt:P279* wd:Q45722.

  # Filter to only the earliest cardinal position
  FILTER(?cardinalStartTime = ?earliestCardinalStartTime)

  FILTER(?birthDate > "1900-01-01"^^xsd:dateTime)
  FILTER(NOT EXISTS { ?cardinal wdt:P570 ?deathDate. })

  OPTIONAL { ?cardinal wdt:P19 ?birthPlace. }
  OPTIONAL {
    ?cardinal p:P106 ?bishopPosition.
    ?bishopPosition ps:P106 wd:Q611644;
                    pq:P580 ?bishopStartTime.
  }
  OPTIONAL {
    ?cardinal p:P106 ?priestPosition.
    ?priestPosition ps:P106 wd:Q250867;
                    pq:P580 ?priestStartTime.
  }

  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],it". }
}
ORDER BY (?birthDate)
```

## Differences

As of today (2025-04-27), the differences between the two lists are the following:
  * The date format in the [College of Cardinals Dashboard](https://press.vatican.va/content/salastampa/en/documentation/cardinali---statistiche/dashboard-collegio-cardinalizio.html) is inconsistent, sometimes `DD/MM/YYYY` is used, other times `MM/DD/YYYY` is used. In `vatican_cardinals.csv` we use `YYYY-MM-DD`. For example, Cardinal Jean-Paul Vesco's birth date is 10 March 1962 (displaied as `DD/MM/YYYY`), but the proclamation date is 7 December 2024 (displaied as `MM/DD/YYYY`).
  ![Row for Cardinal Jean-Paul Vesco](https://i.imgur.com/AeRXjb6.png)


  * The date of birth of Cardinal Toribio Ticona Porco ([Q2444070](https://www.wikidata.org/wiki/Q2444070)) is unclear some sources report `1937-04-25` [[1]](https://press.vatican.va/content/salastampa/en/documentation/cardinali_biografie/cardinali_bio_porcoticona_t.html) (used in Wikidata), while other sources report `1937-05-23` [[2](https://www.catholic-hierarchy.org/bishop/btipo.html), [3](https://cardinals.fiu.edu/bios2018.htm#Ticona)] (used in the Vatican list).

## License

The script is (c) 2025 Cristian Consonni and released under the MIT license, see [`LICENSE.md`](https://github.com/CristianCantoro/wikidata-vatican-cardinals/blob/main/LICENSE.md) for details. The data is released under [CC0 1.0 Universal - Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/).

---

## Scraping from HTML source

The data is also available in an HTML table format at [Vatican Press Office](https://press.vatican.va/content/salastampa/it/documentation/cardinali---statistiche/elenco_per_eta.html). The script `vatican_cardinals_from_html.sh` extracts this data using web scraping techniques.

The script:

- Uses `scrape-cli` to extract the HTML table data
- Processes the table rows using `xq` (from yq) to transform them into JSONL format
- For each cardinal, extracts:
  - name
  - URL of their biographical page
  - birth date (converting it to ISO format YYYY-MM-DD)
  - type of cardinal
  - who created them as cardinal
  - country
  - continent
- Saves the output in `vatican_cardinals_from_html.jsonl`

The [output](vatican_cardinals_from_html.jsonl) is in jsonlines format:

```
{"nome":"ACERBI Card. Angelo","url":"https://press.vatican.va/content/salastampa/it/documentation/cardinali_biografie/cardinali_bio_acerbi_a.html","data_di_nascita":"1925-09-23","tipo":"Non Elettore","creato_da":"Francesco","paese":"Italia","continente":"Europa"}
{"nome":"KARLIC Card. Estanislao Esteban","url":"https://press.vatican.va/content/salastampa/it/documentation/cardinali_biografie/cardinali_bio_karlic_ee.html","data_di_nascita":"1926-02-07","tipo":"Non Elettore","creato_da":"Benedetto XVI","paese":"Argentina","continente":"America del Sud"}
{"nome":"WAMALA Card. Emmanuel","url":"https://press.vatican.va/content/salastampa/it/documentation/cardinali_biografie/cardinali_bio_wamala_e.html","data_di_nascita":"1926-12-15","tipo":"Non Elettore","creato_da":"S. Giovanni Paolo II","paese":"Uganda","continente":"Africa"}
...
```
