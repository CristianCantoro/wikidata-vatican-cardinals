#!/usr/bin/env python3

import argparse
import pathlib
import pandas as pd

def find_missing_cardinals(wikidata_path, vatican_path):
    # Load the two CSV files
    wikidata_df = pd.read_csv(wikidata_path)
    vatican_df = pd.read_csv(vatican_path)

    tmp_wikidata_df = wikidata_df[['cardinalLabel', 'birthDate', 'cardinalStartTime']].copy()
    tmp_wikidata_df.rename({'cardinalLabel': 'fullname',
                            'birthDate': 'birthdate',
                            'cardinalStartTime': 'cardinal_start'
                            }, axis=1, inplace=True)
    tmp_wikidata_df["fullname"] = tmp_wikidata_df["fullname"].apply(lambda x: x.strip().lower())
    tmp_wikidata_df["birthdate"] = (pd.to_datetime(tmp_wikidata_df["birthdate"], errors='coerce')
                                    .dt.date)
    tmp_wikidata_df["cardinal_start"] = (pd.to_datetime(tmp_wikidata_df["cardinal_start"], errors='coerce')
                                         .dt.date)
    sel_wikidata_df = tmp_wikidata_df[['fullname', 'birthdate', 'cardinal_start']] 

    tmp_vatican_df = vatican_df[['Cognome', 'Nome', 'Data di nascita', 'Creato il']].copy()
    tmp_vatican_df.rename({'Cognome': 'surname',
                           'Nome': 'name',
                           'Data di nascita': 'birthdate',
                           'Creato il': 'cardinal_start'
                           }, axis=1, inplace=True)
    tmp_vatican_df["fullname"] = (tmp_vatican_df["name"].apply(lambda x: x.strip().lower()) + \
                                  " " + \
                                  tmp_vatican_df["surname"].apply(lambda x: x.strip().lower()))
    tmp_vatican_df["birthdate"] = (pd.to_datetime(tmp_vatican_df["birthdate"], errors='coerce')
                                   .dt.date)
    tmp_vatican_df["cardinal_start"] = (pd.to_datetime(tmp_vatican_df["cardinal_start"], errors='coerce')
                                        .dt.date)
    sel_vatican_df  = tmp_vatican_df[['fullname', 'birthdate', 'cardinal_start']] 

    import ipdb; ipdb.set_trace()

    # Cardinals in the Vatican list, missing in Wikidata 
    wikidata_names = set(sel_wikidata_df['fullname'].tolist())
    missing_wikidata_cardinals = sel_vatican_df[~sel_vatican_df.apply(
        lambda row: (row['fullname']) in wikidata_names,
        axis=1
    )]

    if len(missing_wikidata_cardinals) > 0:
        missing_wikidata_cardinals.to_csv('missing_' + wikidata_path.name, index=False)

    # Cardinals in Wikidata, missing in the Vatican list 
    vatican_names = set(sel_vatican_df['fullname'].tolist())
    missing_vatican_cardinals = sel_wikidata_df[~sel_wikidata_df.apply(
        lambda row: (row['fullname']) in vatican_names,
        axis=1
    )]

    if len(missing_vatican_cardinals) > 0:
        missing_vatican_cardinals.to_csv('missing_' + vatican_path.name, index=False)

    common_cardinals = sel_vatican_df[sel_vatican_df.apply(
        lambda row: (row['fullname']) in wikidata_names,
        axis=1
    )]
    sel_wikidata_df = sel_wikidata_df.set_index('fullname')
    common_cardinals = common_cardinals.set_index('fullname')
    cardinals_join = common_cardinals.join(sel_wikidata_df,
                                           on='fullname',
                                           lsuffix='_all',
                                           rsuffix='_wd'
                                           )

    different_birth = cardinals_join[cardinals_join['birthdate_all'] != cardinals_join['birthdate_wd']]
    different_start = cardinals_join[cardinals_join['cardinal_start_all'] != cardinals_join['cardinal_start_wd']]

    if len(different_birth) > 0:
        different_birth.to_csv('different_birthdate_'+ wikidata_path.name, index=True)

    if len(different_start) > 0:
        different_start.to_csv('different_cardinal_start_'+ wikidata_path.name, index=True)

    return


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("wikidata",
                        metavar="<wikidata>",
                        type=pathlib.Path,
                        help="Wikidata data"
                        )
    parser.add_argument("vatican",
                        metavar="<vatican>",
                        type=pathlib.Path,
                        help="Vatican data"
                        )
    args = parser.parse_args()

    return args


if __name__ == '__main__':

    args = cli()

    # Example usage:
    find_missing_cardinals(args.wikidata, args.vatican)
