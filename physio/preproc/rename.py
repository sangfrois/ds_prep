# -*- coding: utf-8 -*-
# !/usr/bin/env python -W ignore::DeprecationWarning
"""Neuromod phys data rename converted files."""

import glob
import pandas as pd
import argparse
import sys
import os

def _get_parser():
    """
    Parse command line inputs for this function.

    Returns
    -------
    parser.parse_args() : argparse dict
    Notes
    -----
    # Argument parser follow template provided by RalphyZ.
    # https://stackoverflow.com/a/43456577
    """
    parser = argparse.ArgumentParser()
    optional = parser._action_groups.pop()
    required = parser.add_argument_group('Required Argument:')

    required.add_argument('-indir', '--input-directory',
                          dest='scratch',
                          type=str,
                          help='Specify where you want to save the converted dataset',
                          default=None)
    required.add_argument('-sub', '--subject',
                          dest='sub',
                          type=str,
                          help='Specify subject number, e.g. sub-01')
    optional.add_argument('-ses', '--session',
                          dest='sessions',
                          type=str,
                          help='Specify session number, e.g. ses-001')
    return parser


def co_register_physio(scratch, sub, sessions=None):
    """
    Comply to BIDS and co-register functional acquisitions.

    Rename valid files and remove invalid files for 1 subject's directory

    Parameters:
    ------------
    scratch : path
        directory to save data and to retrieve acquisition info (`.json file`)
    subject : string
        name of path for a specific subject (e.g.'sub-03')
    sessions : list
        specific session numbers can be listed (e.g. ['ses-001', 'ses-002']
    Returns:
    --------
    BIDS-compliant /func directory for physio files
    """
    # fetch info
    info = pd.read_json(f"{scratch}{sub}/{sub}_volumes_all-ses-runs.json")
    # define sessions
    if sessions is None:
        sessions = info.columns
    else:
        sessions = [sessions]

    # iterate through sesssions
    for ses in sessions:
        # list files in the session
        tsv = glob.glob(f"{scratch}{sub}/{ses}/*.tsv.gz")
        json = glob.glob(f"{scratch}{sub}/{ses}/*.json")
        log = glob.glob(f"{scratch}{sub}/{ses}/code/conversion/*.log")
        png = glob.glob(f"{scratch}{sub}/{ses}/code/conversion/*.png")

        # check sanity of info
        if ses['expected_runs'] is not ses['processed_runs']:
            raise(f"Expected number of runs {ses['expected_runs']} "
                  "does not match info from neuroimaging metadata")
        elif len(ses['tasks']) is not ses['expected_runs']:
            raise("Number of tasks does not match expected number of runs")
        elif ses['recorded_triggers'].values is None:
            raise("No recorded triggers information - check physio files")

        # if input is normal, then check co-registration
        else:
            triggers = ses['recorded_triggers'].values()
            # remove files that don't contain enough volumes
            for idx, volumes in enumerate(triggers):
                if volumes < 400:
                    os.remove(tsv[idx])
                    os.remove(json[idx])
                    os.remove(log[idx])
                    os.remove(png[idx])
                    triggers.pop(idx)
            # check if number of volumes matches neuroimaging JSON sidecar
            for idx, volumes in enumerate(triggers):
                if volumes is not ses[f'{idx+1:02d}']:
                    raise(f"Recorded triggers info for {ses[idx+1:02d]}")
                else:
                    os.rename(tsv[idx],
                              f"{sub}_{ses}_{ses['tasks'][idx]}_physio.tsv.gz")
                    os.rename(json[idx],
                              f"{sub}_{ses}_{ses['tasks'][idx]}_physio.json")


def _main(argv=None):
    options = _get_parser().parse_args(argv)
    co_register_physio(**vars(options))


if __name__ == '__main__':
    _main(sys.argv[1:])
