#!/usr/bin/env python3

import argparse
import pathlib
import pandas as pd
from rapidfuzz import process, fuzz

DEFAULT_OUTPUT_DIR = pathlib.Path('output')

def fuzzy_match_dataframes(df1, df2):
    matches = []

    for idx1, row1 in df1.iterrows():
        fullname1 = row1['fullname']
        birthdate1 = row1['birthdate']
        cardinal_start1 = row1['cardinal_start']

        # Build list of choices for matching
        choices = df2['fullname'].tolist()


        try:
            # Find best match using rapidfuzz
            match, score, idx2 = process.extractOne(
                fullname1,
                choices,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=66  # You can tweak this cutoff
            )
        except:
            match = None
            score = 0

        if match:
            matched_row = df2.iloc[idx2]

            # Additional check: birthdate and cardinal_start
            if (birthdate1 == matched_row['birthdate']) and (cardinal_start1 == matched_row['cardinal_start']):
                matches.append({
                    'df1_index': idx1,
                    'df2_index': idx2,
                    'fullname_df1': fullname1,
                    'fullname_df2': match,
                    'score': score
                })

    # Convert matches to a dataframe
    matches_df = pd.DataFrame(matches)

    return matches_df


def write_results_csv(res_df, output_name, output_dir, index=False):
    if len(res_df) > 0:
        output_dir.mkdir(parents=True, exist_ok=True)
        res_df.to_csv(output_dir / output_name, index=index)


def find_missing_cardinals(wikidata_path, vatican_path, output_dir):
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

    # Cardinals in the Vatican list, missing in Wikidata 
    wikidata_names = set(sel_wikidata_df['fullname'].tolist())
    missing_wikidata_cardinals = sel_vatican_df[~sel_vatican_df.apply(
        lambda row: (row['fullname']) in wikidata_names,
        axis=1
    )]

    matches_df = fuzzy_match_dataframes(sel_wikidata_df, missing_wikidata_cardinals)
    matches_names_wd = set(matches_df['fullname_df2'].tolist())
    missing_wikidata_cardinals2 = (missing_wikidata_cardinals[~(missing_wikidata_cardinals['fullname']
                                                                .isin(matches_names_wd))])

    merge_matches_tmp1 = matches_df.merge(sel_wikidata_df,
                                         left_on='df1_index',
                                         right_index=True
                                         )
    merge_matches_tmp2 = merge_matches_tmp1.merge(sel_vatican_df,
                                                left_on='fullname_df2',
                                                right_on='fullname',
                                                suffixes=('_wd', '_va')
                                                )
    fuzzymatch_df = merge_matches_tmp2[['fullname_wd', 'birthdate_wd', 'cardinal_start_wd',
                                        'fullname_va', 'birthdate_va', 'cardinal_start_va',
                                        'score']]

    write_results_csv(fuzzymatch_df, 'fuzzymatch_'+wikidata_path.name, output_dir)
    write_results_csv(missing_wikidata_cardinals2, 'missing_'+wikidata_path.name, output_dir)

    # Cardinals in Wikidata, missing in the Vatican list 
    vatican_names = set(sel_vatican_df['fullname'].tolist())
    missing_vatican_cardinals = sel_wikidata_df[~sel_wikidata_df.apply(
        lambda row: (row['fullname']) in vatican_names,
        axis=1
    )]

    matches_names_va = set(matches_df['fullname_df1'].tolist())
    missing_vatican_cardinals2 = (missing_vatican_cardinals[~(missing_vatican_cardinals['fullname']
                                                              .isin(matches_names_va))])

    write_results_csv(missing_vatican_cardinals2, 'missing_'+vatican_path.name, output_dir)

    common_cardinals = sel_vatican_df[sel_vatican_df.apply(
        lambda row: (row['fullname']) in wikidata_names,
        axis=1
    )]
    sel_wikidata_df = sel_wikidata_df.set_index('fullname')
    common_cardinals = common_cardinals.set_index('fullname')
    cardinals_join = common_cardinals.join(sel_wikidata_df,
                                           on='fullname',
                                           lsuffix='_va',
                                           rsuffix='_wd'
                                           )

    different_birth = cardinals_join[
        cardinals_join['birthdate_va'] != cardinals_join['birthdate_wd']
        ]
    different_start = cardinals_join[
        cardinals_join['cardinal_start_va'] != cardinals_join['cardinal_start_wd']
        ]

    write_results_csv(different_birth,
                      'different_birthdate_'+wikidata_path.name,
                      output_dir,
                      index=True
                      )
    write_results_csv(different_start,
                      'different_cardinal_start_'+wikidata_path.name,
                      output_dir,
                      index=True
                      )

    return


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("wikidata",
                        metavar="<wikidata>",
                        type=pathlib.Path,
                        help="Wikidata data."
                        )
    parser.add_argument("vatican",
                        metavar="<vatican>",
                        type=pathlib.Path,
                        help="Vatican data."
                        )
    parser.add_argument("--output-dir",
                        type=pathlib.Path,
                        default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory [default: {DEFAULT_OUTPUT_DIR}]."
                        )

    args = parser.parse_args()

    return args


if __name__ == '__main__':

    args = cli()

    # Example usage:
    find_missing_cardinals(args.wikidata, args.vatican, output_dir=args.output_dir)
