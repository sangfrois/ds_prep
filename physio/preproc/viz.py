# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
Neuromod processing utilities
"""
# dependencies
from neuromod_process import neuromod_bio_process
from bokeh.plotting import output_file, save
from systole import plots
import sys
import argparse
import glob
import pandas as pd
import os
import pickle

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
                          dest='indir',
                          type=str,
                          help='Specify the location of the converted dataset',
                          default=None)
    required.add_argument('-outdir', '--output-directory',
                          dest='outdir',
                          type=str,
                          help='Specify where you want to save the viz',
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

def neuromod_ppg_viz(indir, outdir, sub, sessions=None):
    """
   Results for one subject data


    Parameters:
    ------------
    indir : path
        main directory containing the biopac data (e.g. /to/dataset/info)
    outdir : path
        directory to save data and to retrieve acquisition info (`.json file`)
    subject : string
        name of path for a specific subject (e.g.'sub-03')
    sessions : list
        specific session numbers can be listed (e.g. ['ses-001', 'ses-002']
    Returns:
    --------
    results output
    """
    if sessions is None:
        info = pd.read_json(f"{indir}{sub}/{sub}_volumes_all-ses-runs.json")
        sessions = info.columns
    elif isinstance(sessions, list) is False:
        sessions = [sessions]
    for ses in sessions:
        print(f"Currently processing {ses}")
        
        tsv = glob.glob(f"{indir}{sub}/{ses}/*.tsv.gz")
        tsv.sort()
        
        json = glob.glob(f"{indir}{sub}/{ses}/*.json")
        json.sort()
                
        for bio, sidecar in zip(tsv, json):
            fn = bio[bio.rfind('/')+1:-7]
            sidecar = pd.read_json(sidecar)
            bio_df = pd.read_csv(f"{bio}",
                                 sep='\t',
                                 compression='gzip',
                                 header=None,
                                 names=sidecar.Columns)
            fs = sidecar['SamplingFrequency'][0]
            
            signals, info_corrected = neuromod_bio_process(df=bio_df, sampling_rate=fs)
           
            plot = plots.plot_raw(signals['PPG_Clean'], backend='bokeh',
                                  show_heart_rate=True, show_artefacts=True, sfreq=fs)
            
            if os.path.isdir(f'{outdir}') is False:
                os.mkdir(f'{outdir}')
                print("Created output directory")
            if os.path.isdir(f'{outdir}{sub}') is False:
                os.mkdir(f'{outdir}{sub}')
                print(f"Created output directory for {sub}")
            if os.path.isdir(f'{outdir}{sub}/{ses}') is False:
                os.mkdir(f'{outdir}{sub}/{ses}')
                print(f"Created output directory for {ses}")
            
            signals.to_csv(f'{outdir}{sub}/{ses}/{sub}_{ses}_{fn}_physio-signals.tsv.gz', sep='\t', index=False,
                           compression='gzip')
            print(f"Signals are saved with columns : {signals.columns}")
            
            with open(f'{outdir}{sub}/{ses}/{sub}_{ses}_{fn}_physio-info.json', 'wb') as fp:
                pickle.dump(info_corrected, fp)
            print(f"Info are saved with these features : {info_corrected.keys()}")
                
            output_file(f"{outdir}{sub}/{ses}/{fn}.html")
            save(plot)
            
            print(f"Done with {ses}, run-{fn[-2:]}")
    
    print('done')
    
def _main(argv=None):
    options = _get_parser().parse_args(argv)
    neuromod_ppg_viz(**vars(options))


if __name__ == '__main__':
    _main(sys.argv[1:])
