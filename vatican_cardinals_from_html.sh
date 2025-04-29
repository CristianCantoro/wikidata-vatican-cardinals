#!/bin/bash

# -----------------------------------------------------
# Extract the list of Cardinals in JSONL format
# Requirements:
# - yq (https://github.com/kislyuk/yq) → provides the `xq` command
# - scrape-cli (https://github.com/aborruso/scrape-cli)
# -----------------------------------------------------

set -euo pipefail

# Check if required commands are available
command -v scrape >/dev/null 2>&1 || {
  echo >&2 "Error: 'scrape' is not installed. See https://github.com/aborruso/scrape-cli"
  exit 1
}

command -v xq >/dev/null 2>&1 || {
  echo >&2 "Error: 'xq' (from yq kislyuk) is not installed. See https://github.com/kislyuk/yq"
  exit 1
}

# Source URL
URL="https://press.vatican.va/content/salastampa/it/documentation/cardinali---statistiche/elenco_per_eta.html"

# Extract and save in JSONL
curl -kLs "$URL" \
  | scrape -be '//table[@cellspacing="10"]//tr[position() > 2]' \
  | xq -c '
    .html.body.tr[]
    | select(.td | length > 6)
    | {
        nome: .td[1].div.a["#text"],
        url: "https://press.vatican.va\(.td[1].div.a["@href"])",
        data_di_nascita: (
          .td[2]
          | split("-")
          | "\(.[2])-\(.[1])-\(.[0])"
        ),
        tipo: .td[3],
        creato_da: .td[4],
        paese: .td[5],
        continente: .td[6]
      }
  ' > vatican_cardinals_from_html.jsonl

echo "✅ Data saved in vatican_cardinals_from_html.jsonl"
