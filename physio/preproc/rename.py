# -*- coding: utf-8 -*-
# !/usr/bin/env python -W ignore::DeprecationWarning
"""Neuromod phys data rename converted files."""

import glob
import pandas as pd
import numpy as np
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
        print(f"renaming files in session : {ses}")
        
        # list files in the session
        tsv = glob.glob(f"{scratch}{sub}/{ses}/*.tsv.gz")
        tsv.sort()

        if tsv is None:
            print(f"no physio file for {ses}")
            continue

        json = glob.glob(f"{scratch}{sub}/{ses}/*.json")
        json.sort()

        log = glob.glob(f"{scratch}{sub}/{ses}/code/conversion/*.log")
        log.sort()

        png = glob.glob(f"{scratch}{sub}/{ses}/code/conversion/*.png")
        png.sort()

        # check sanity of info - expected runs is number of runs in BOLD sidecar
        if info[ses]['expected_runs'] is not info[ses]['processed_runs']:
            print(f"Expected number of runs {info[ses]['expected_runs']} "
                  "does not match info from neuroimaging metadata")

        if len(info[ses]['task']) is not info[ses]['expected_runs']:
            print("Number of tasks does not match expected number of runs")
            continue
            
        if info[ses]['recorded_triggers'].values is None:
            print(f"No recorded triggers information - check physio files for {ses}")
            continue

        # if input is normal, then check co-registration
        else:
            # sanitize list
            triggers = list(info[ses]['recorded_triggers'].values())
            triggers = list(np.concatenate(triggers).flat)
            
            to_be_del = []
            
            # remove files that don't contain enough volumes
            for idx, volumes in enumerate(triggers):
                # NOTE: this should not be hardcoded 
                if volumes < 400:
                    to_be_del.append(idx)
            
            # these can be safely removed
            for idx in to_be_del:
                os.remove(tsv[idx])
                os.remove(json[idx])
                os.remove(log[idx])
                os.remove(png[idx])
            
            # theses are to be kept
            triggers = np.delete(triggers, to_be_del)
            tsv = np.delete(tsv, to_be_del)
            json = np.delete(json, to_be_del)
            log = np.delete(log, to_be_del)
            png = np.delete(png, to_be_del)

            

            # check if number of volumes matches neuroimaging JSON sidecar
            for idx, volumes in enumerate(triggers):
                print(info[ses][f'{idx+1:02d}'])
                if volumes != info[ses][f'{idx+1:02d}']:
                    print(f"Recorded triggers info for {ses} does not match with "
                          f"BOLD sidecar ({volumes} != {info[ses][idx+1:02d]})")
                    continue

                else:
                    os.rename(tsv[idx],
                              f"{scratch}{sub}/{ses}/{sub}_{ses}_{info[ses]['task'][idx]}_physio.tsv.gz")
                    os.rename(json[idx],
                              f"{scratch}{sub}/{ses}/{sub}_{ses}_{info[ses]['task'][idx]}_physio.json")


def _main(argv=None):
    options = _get_parser().parse_args(argv)
    co_register_physio(**vars(options))


if __name__ == '__main__':
    _main(sys.argv[1:])
