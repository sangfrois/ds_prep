# -*- coding: utf-8 -*-
# !/usr/bin/env python -W ignore::DeprecationWarning
"""Neuromod phys data conversion."""

from phys2bids.phys2bids import phys2bids
import argparse
import sys
import pandas as pd
import gc

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
                          dest='sourcedata',
                          type=str,
                          help='Specify where you want to save the converted dataset',
                          default=None)
    required.add_argument('-outdir', '--output-directory',
                          dest='scratch',
                          type=str,
                          help='Specify root directory of dataset where sourcedata stands',
                          default=None)
    required.add_argument('-sub', '--subject',
                          dest='sub',
                          type=str,
                          help='Specify subject number, e.g. sub-01')
    # optional
    optional.add_argument('-ses', '--session',
                          dest='sessions',
                          nargs='*',
                          type=str,
                          help='Specify session number, e.g. ses-001')
    return parser

def neuromod_phys2bids(sourcedata, scratch, sub, sessions=None):
    """
    Phys2Bids conversion for one subject data


    Parameters:
    ------------
    sourcedata : path
        main directory containing the biopac data (e.g. /to/dataset/info)
    scratch : path
        directory to save data and to retrieve acquisition info (`.json file`)
    subject : string
        name of path for a specific subject (e.g.'sub-03')
    sessions : list
        specific session numbers can be listed (e.g. ['ses-001', 'ses-002']
    Returns:
    --------
    phys2bids output
    """
    # fetch info
    info = pd.read_json(f"{scratch}{sub}/{sub}_volumes_all-ses-runs.json")
    # define sessions
    if sessions is None:
        sessions = info.columns
    elif isinstance(sessions, list) is False:
        sessions = [sessions]
    # iterate through info
    for col in sessions:
        # skip empty sessions
        if info[col] is None:
            continue
        print(col)

        # Iterate through files in each session and run phys2bids
        filename = info[col]['in_file']
        if filename is list:
            for i in range(len(filename)-1):
                phys2bids(
                        filename[i],
                        info=False,
                        indir=f'{sourcedata}/{sub}/{col}/',
                        outdir=f'{scratch}/{sub}/{col}',
                        heur_file=None,
                        sub=sub[-2:],
                        ses=col[-3:],
                        chtrig=4,
                        chsel=None,
                        num_timepoints_expected=info[col]['recorded_triggers'][
                                                          f'run-0{i+1}'],
                        tr=1.49,
                        thr=4,
                        pad=9,
                        ch_name=["EDA", "PPG", "ECG", "TTL", "RSP"],
                        yml='',
                        debug=False,
                        quiet=False)
        else:
            try:
                phys2bids(
                    filename,
                    info=False,
                    indir=f'{sourcedata}physio/{sub}/{col}/',
                    outdir=f'{scratch}/{sub}/{col}',
                    heur_file=None,
                    sub=sub[-2:],
                    ses=col[-3:],
                    chtrig=4,
                    chsel=None,
                    num_timepoints_expected=info[col]['recorded_triggers'][
                                                      'run-01'],
                    tr=1.49,
                    thr=4,
                    pad=9,
                    ch_name=["EDA", "PPG", "ECG", "TTL", "RSP"],
                    yml='',
                    debug=False,
                    quiet=False,
                )
            except AttributeError:
                filename.sort()
                for i in range(len(filename)):
                    print(i)
                    phys2bids(
                        filename[i],
                        info=False,
                        indir=f'{sourcedata}/{sub}/{col}/',
                        outdir=f'{scratch}/{sub}/{col}',
                        heur_file=None,
                        sub=sub[-2:],
                        ses=col[-3:],
                        chtrig=4,
                        chsel=None,
                        num_timepoints_expected=info[col]['recorded_triggers'][
                                                          f'run-0{i+1}'],
                        tr=1.49,
                        thr=4,
                        pad=9,
                        ch_name=["EDA", "PPG", "ECG", "TTL", "RSP"],
                        yml='',
                        debug=False,
                        quiet=False)

            except TypeError:
                print(f"No input file for {col}") 
                continue
        gc.collect()
        print("~"*30)

def _main(argv=None):
    options = _get_parser().parse_args(argv)
    neuromod_phys2bids(**vars(options))


if __name__ == '__main__':
    _main(sys.argv[1:])
