from phys2bids.phys2bids import phys2bids
import argparse
import sys
import pandas as pd

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
                          dest='root',
                          type=str,
                          help='Specify root directory of dataset',
                          default=None)
    required.add_argument('-sub', '--subject',
                          dest='sub',
                          type=str,
                          help='Specify alongside \"-heur\". Code of '
                               'subject to process.')
    required.add_argument('-ses', '--session',
                          dest='sessions',
                          type=str,
                          help='Specify alongside \"-heur\". Code of '
                               'sessions to process.')
    return parser

def neuromod_phys2bids(root, sub, sessions=None):
    """
    Phys2Bids conversion for one subject data

    
    Parameters:
    ------------
    root : path
        main directory containing the biopac data (e.g. /to/dataset/sourcedata)
    subject : string
        name of path for a specific subject (e.g.'sub-03')
    sessions : list
        specific session numbers can be listed (e.g. ['ses-001', 'ses-002']
    Returns:
    --------
    phys2bids output
    """
    info = pd.read_json(f"{root}{sub}/{sub}_volumes_all-ses-runs.json")
    if sessions is None:
        sessions = info.columns
    else:
        sessions = [sessions]
    for col in sessions:
        if col is None:
            continue
        print(col)
        filename=info[col]['in_file']
        if filename is list:
            for i in range (len(filename)-1):
                print(i)
                phys2bids(
                        filename[i],
                        info=False,
                        indir=f'/data/neuromod/DATA/cneuromod/friends/sourcedata/physio/{sub}/{col}/',
                        outdir=f'/scratch/flesp/physio_data/friends/{sub}/{col}',
                        heur_file=None,
                        sub=sub[-2:],
                        ses=col[-3:],
                        chtrig=4,
                        chsel=None,
                        num_timepoints_expected=info[col]['recorded_triggers'][f'run-0{i+1}'],
                        tr=1.49,
                        thr=4,
                        pad=9,
                        ch_name=["EDA", "PPG", "ECG", "TTL", "RSP" ],
                        yml='',
                        debug=False,
                        quiet=False,
                    )
        else:
             try:
                 phys2bids(
                    filename,
                    info=False,
                    indir=f'/data/neuromod/DATA/cneuromod/friends/sourcedata/physio/{sub}/{col}/',
                    outdir=f'/scratch/flesp/physio_data/friends/{sub}/{col}',
                    heur_file=None,
                    sub=sub[-2:],
                    ses=col[-3:],
                    chtrig=4,
                    chsel=None,
                    num_timepoints_expected=info[col]['recorded_triggers']['run-01'],
                    tr=1.49,
                    thr=4,
                    pad=9,
                    ch_name=["EDA", "PPG", "ECG", "TTL", "RSP" ],
                    yml='',
                    debug=False,
                    quiet=False,
                )
             except TypeError:
                 print(f'skipping {col} because no input file given')
                 continue
             except AttributeError:
                 for i in range (len(filename)):
                     print(i)
                     phys2bids(
                        filename[i],
                        info=False,
                        indir=f'/data/neuromod/DATA/cneuromod/friends/sourcedata/physio/{sub}/{col}/',
                        outdir=f'/scratch/flesp/physio_data/friends/{sub}/{col}',
                        heur_file=None,
                        sub=sub[-2:],
                        ses=col[-3:],
                        chtrig=4,
                        chsel=None,
                        num_timepoints_expected=info[col]['recorded_triggers'][f'run-0{i+1}'],
                        tr=1.49,
                        thr=4,
                        pad=9,
                        ch_name=["EDA", "PPG", "ECG", "TTL", "RSP" ],
                        yml='',
                        debug=False,
                        quiet=False,
                    )   
        print("~"*30)        

def _main(argv=None):
    options = _get_parser().parse_args(argv)
    neuromod_phys2bids(**vars(options))


if __name__ == '__main__':
    _main(sys.argv[1:])

