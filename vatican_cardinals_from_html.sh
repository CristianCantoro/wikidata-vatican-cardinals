#!/bin/bash

# Usage: ./vatican_cardinals_from_html.sh
#
# -----------------------------------------------------------------------------
# Extract the list of Cardinals in JSONL format
# Requirements:
# - yq (https://github.com/kislyuk/yq) → provides the `xq` command
# - scrape-cli (https://github.com/aborruso/scrape-cli)
# - csvgormat from csvkit (https://github.com/wireservice/csvkit)
# -----------------------------------------------------------------------------

set -euo pipefail

# Source URL
URL="https://press.vatican.va/content/salastampa/it/documentation/cardinali---statistiche/elenco_per_eta.html"

function short_usage {
  (>&2 echo \
"Usage:
  $(basename "$0") [-o OUTPUT_FILE] [--csv]
  $(basename "$0") (-h | --help)")
}

function usage {
  (>&2 short_usage )
  (>&2 echo \
"
Extract the list of Cardinals in JSONL or CSV format from:
$URL

Options:
  -o OUTPUT_FILE,               Output file name [default: vatican_cardinals_from_html.<ext>]
  --output-file OUTPUT_FILE
  --csv                         Convert the results into CSV.
  -h, --help                    Show this help and exits.
")
}

# Check if required commands are available
command -v scrape >/dev/null 2>&1 || {
  (echo >&2 "Error: 'scrape' is not installed. " \
            "See https://github.com/aborruso/scrape-cli")
  exit 1
}

command -v xq >/dev/null 2>&1 || {
  (echo >&2 "Error: 'xq' (from yq kislyuk) is not installed. " \
            "See https://github.com/kislyuk/yq")
  exit 1
}

command -v csvformat >/dev/null 2>&1 || {
  (echo >&2 "Error: 'csvformat' (from csvkit) is not installed. " \
            "See https://github.com/wireservice/csvkit")
  exit 1
}

help_flag=false
output_file='vatican_cardinals_from_html.<ext>'
format='jsonl'

while getopts ":ho:-:" OPT; do
  # support long options
  #   https://stackoverflow.com/a/28466267/519360
  #
  # long option: reformulate OPT and OPTARG
  if [ "$OPT" = "-" ]; then
    # extract long option name
    OPT="${OPTARG%%=*}"
    # extract long option argument (may be empty)
    OPTARG="${OPTARG#"$OPT"}"
    # if long option argument, remove assigning `=`
    OPTARG="${OPTARG#=}"
  fi
  case "$OPT" in
    csv)
      format='csv'
      ;;
    o|output-file)
      output_file="$OPTARG"
      ;;
    h|help)
      help_flag=true
      ;;
    \?)
      (>&2 echo "Error. Invalid option: -$OPTARG")
      short_usage
      exit 2
      ;;
    :)
      (>&2 echo "Error.Option -$OPTARG requires an argument.")
      short_usage
      exit 1
      ;;
    *)
      # bad long option
      (>&2 echo "Illegal option --$OPT")
      short_usage
      exit 1
      ;;
  esac
done

if $help_flag; then
  usage
  exit 0
fi
#################### end: help

tmpdir=$(mktemp -d -t tmp.vatican_cardinals_from_html.XXXXXXXXXX)
function cleanup {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

if [[ "$output_file" =~ ".<ext>" ]]; then
  output_file="$(echo 'vatican_cardinals_from_html.<ext>' | sed -r "s#<ext>#$format#")"
fi

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
  ' > "${tmpdir}/vatican_cardinals_from_html.jsonl"

if [[ "$format" == "jsonl" ]]; then
  cp "${tmpdir}/vatican_cardinals_from_html.jsonl" "${output_file}"
elif [[ "$format" == "csv" ]]; then
  # Extract headers (keys) from the first line
  csv_headers=$(head -n 1 "${tmpdir}/vatican_cardinals_from_html.jsonl" | \
                jq -r 'keys_unsorted | @csv')

  # Write headers to CSV
  echo "$csv_headers" > "${tmpdir}/vatican_cardinals_from_html.csv"

  # Convert each JSON object to CSV row
  while IFS= read -r line; do
    echo "$line" | jq -r '[.[]] | @csv' >> "${tmpdir}/vatican_cardinals_from_html.csv"
  done < "${tmpdir}/vatican_cardinals_from_html.jsonl"

  csvformat -u 0 -D',' "${tmpdir}/vatican_cardinals_from_html.csv" >> "${output_file}"
fi

echo "✅ Data saved in $output_file"

exit 0
