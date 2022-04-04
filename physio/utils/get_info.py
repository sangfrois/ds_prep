# -*- coding: utf-8 -*-
# !/usr/bin/env python -W ignore::DeprecationWarning
"""another util for neuromod phys data conversion."""
import pprintpp
import glob
import sys
from list_sub import list_sub
import json
import logging
from CLI import _get_parser2
from pandas import read_csv, errors
import os
from neurokit2 import read_acqknowledge

LGR = logging.getLogger(__name__)


def volume_counter(root, subject, ses=None):
    """
    Volume counting for each run in a session.

    Make sure the trigger channel is named "TTL" because it is hard-coded
    Parameters:
    ------------
    root : path
        main directory containing the biopac data (e.g. /to/dataset/sourcedata)
    subject : string
        name of path for a specific subject (e.g.'sub-03')
    ses : string
        name of acquisition session. Optional workflow for specific experiment
        default is None
    Returns:
    --------
    ses_runs: dictionary
        each key lists the number of volumes in each run, including invalids
    """
    # Check directory
    if os.path.exists(root) is False:
        raise ValueError("Couldn't find the following directory: ",  root)

    # List the files that have to be counted
    dirs = list_sub(root, subject, ses)
    ses_runs = {}
    # loop iterating through files in each dict key representing session
    # returned by list_sub
    # for this loop, exp refers to session's name,
    # avoiding confusion with ses argument
    for exp in dirs:
        print("counting volumes in physio file for:", exp)
        for file in sorted(dirs[exp]):
            # reading acq
            bio_df, fs = read_acqknowledge(os.path.join(
                                       root, subject, exp, file))  # resampling

            # initialize a df with TTL values over 4 (switch either ~0 or ~5)
            query_df = bio_df[bio_df[bio_df.columns[3]] > 4]

            # Define session length - this list will be less
            # memory expensive to play with than dataframe
            session = list(query_df.index)

            # maximal TR - the time (2s) distance between two adjacent TTL
            tr_period = fs * 2

            # Define session length and adjust with padding
            start = int(session[0])
            end = int(session[-1])

            # initialize list of sample index to compute nb of volumes per run
            parse_list = []

            # ascertain that session is longer than 3 min
            for idx in range(1, len(session)):
                # define time diff between current successive trigger
                time_delta = session[idx] - session[idx-1]

                # if the time diff between two trigger values over 4
                # is larger than TR, keep both indexes
                if time_delta > tr_period:
                    parse_start = int(session[idx-1])
                    parse_end = int(session[idx])
                    # adjust the segmentation with padding
                    # parse start is end of run
                    parse_list += [(parse_start, parse_end)]
            if len(parse_list)==0:
                runs=round((end-start)/fs/1.49+1)
                if exp not in ses_runs:
                    ses_runs[exp] = [runs]
                else:
                    ses_runs[exp].append([runs])
                continue
            # Create tuples with the given indexes
            # First block is always from first trigger to first parse
            block1 = (start, parse_list[0][0])

            # runs is a list of tuples specifying runs in the session
            runs = []
            # push the resulting tuples (run_start, run_end)
            runs.append(block1)
            for i in range(0, len(parse_list)):
                try:
                    runs.append((parse_list[i][1], parse_list[1+i][0]))

                except IndexError:
                    runs.append((parse_list[i][1], end))

            # compute the number of trigger/volumes in the run
            for i in range(0, len(runs)):
                runs[i] = round(((runs[i][1]-runs[i][0])/fs)/1.49)+1
            if exp not in ses_runs:
                ses_runs[exp] = [runs]
            else:
                ses_runs[exp].append(runs)

    return ses_runs


def get_info(root=None, sub=None, ses=None, count_vol=False, show=True,
             save=None, scanning_sheet=None):
    """
    Get all volumes taken for a sub.

    get_info pushes the info necessary to execute the phys2bids multi-run
    workflow to a dictionary. It can save it to `_volumes_all-ses-runs.json`
    in a specified path, or be printed in your terminal.

    Arguments
    ---------
    root : str BIDS CODE
        root directory of dataset, like "home/user/dataset"
    sub : str BIDS CODE
        subject number, like "sub-01"
    ses : str BIDS CODE
        session name or number, like "ses-001"
    count_vol : bool
        Defaults to False. Specify if you want to count triggers in physio file
    show : bool
        Defaults to True. Specify if you want to print the dictionary
    save : path
        Defaults to None and will save at root. Specify where you want to save
        the dictionary in json format
    scanning_sheet : path
        Defaults to None and does not check when missing info. Specify where to
        look for a scanning sheet

    Returns
    -------
    ses_runs_vols : dict
        number of processed runs, number of expected runs, number of trigger or
        volumes per run, sourcedata file location

    Example :
    >>> ses_runs_vols = get_info(root = "/home/user/dataset/", sub = "sub-01")
    """
    # list matches for a whole subject's dir
    ses_runs_matches = list_sub(f"{root}sourcedata/physio/",
                                sub, ses, type='.tsv', show=show)
    ses_info = list_sub(f"{root}sourcedata/physio/",
                        sub, ses, type='.acq')

    # go to fmri matches and get entries for each run of a session
    nb_expected_runs = {}

    # iterate through sessions and get _matches.tsv with list_sub dict
    for exp in ses_runs_matches:
        print(exp)

        # initialize a counter and a dictionary
        nb_expected_volumes_run = {}
        tasks=[]
        matches = glob.glob(f"{root}{sub}/{exp}/func/*bold.json")
        matches.sort()
        # iterate through _bold.json
        for idx, filename in enumerate(matches):
            task = filename.rfind(f"{exp}_")+8
            task_end = filename.rfind("_")
            tasks += [filename[task:task_end]]
            
            # read metadata
            with open(filename) as f:
                bold = json.load(f)
            # we want to GET THE NB OF VOLUMES in the _bold.json of a given run
            try:
                nb_expected_volumes_run[f'{idx+1:02d}'
                                    ] = bold["time"
                                             ]["samples"
                                               ]["AcquisitionNumber"][-1]
            # if it does not work, check scanning sheet or continue
            except KeyError:
                pprintpp.pprint(f"skipping {exp} because .json info non-existant")
                if scanning_sheet is not None:
                    pprintpp.pprint(f"checking scanning sheet for {sub}/{exp}")
                    df_sheet=read_csv(scanning_sheet)
                    vol_idx=df_sheet[df_sheet[sub]==f"p{sub[4:]}_friends{exp[4:]}"].index+idx
                    vols=int(df_sheet["#volumes"].iloc[vol_idx])
                    nb_expected_volumes_run[f'{idx+1:02d}']=vols
                
                else:
                    continue

            
        # print the thing to show progress
        print(nb_expected_volumes_run)
        # push all info in run in dict
        nb_expected_runs[exp] = {}
        # the nb of expected volumes in each run of the session (embedded dict)
        nb_expected_runs[exp] = nb_expected_volumes_run
        nb_expected_runs[exp]['expected_runs'] = len(matches)
        nb_expected_runs[exp]['processed_runs'] = idx  # counter is used here
        nb_expected_runs[exp]['task'] = tasks
        # save the name
        name = ses_info[exp]
        if name:
            name.reverse()
            nb_expected_runs[exp]['in_file'] = name

        if count_vol:
            run_dict = {}
            # check if biopac file exist, notify the user that we won't
            # count volumes
            try:
                # do not count the triggers in phys file if no physfile
                if os.path.isfile(
                     f"{root}sourcedata/physio/{sub}/{exp}/{name[0]}") is False:
                    print('cannot find session directory for sourcedata :',
                          f"{root}sourcedata/physio/{sub}/{exp}/{name[0]}")
                else:
                    # count the triggers in physfile otherwise
                    try:
                        vol_in_biopac = volume_counter(
                                    f"{root}sourcedata/physio/", sub, ses=exp)
                        print("finished counting volumes in physio file for:",
                              exp)

                        for i, run in enumerate(vol_in_biopac[exp]):
                            run_dict.update({f"run-{i+1:02d}": run})

                        nb_expected_runs[exp][
                                      'recorded_triggers'] = run_dict
                        
                    # skip the session if we did not find the _bold.json
                    except KeyError:
                        continue
            except KeyError:
                nb_expected_runs[exp]['recorded_triggers'] = float('nan')
                print('Directory is empty or file is clobbered/No triggers: ',
                      f"{root}sourcedata/physio/{sub}/{exp}/")

                print(f"skipping :{exp} for task {filename}")
        if bool(run_dict):
            print(run_dict)
        print('~'*30)

    if show:
        pprintpp.pprint(nb_expected_runs)
    if save is not None:
        if os.path.exists(f"{save}{sub}") is False:
            os.mkdir(f"{save}{sub}")
        with open(f"{save}{sub}/{sub}_volumes_all-ses-runs.json", 'w') as fp:
            json.dump(nb_expected_runs, fp, sort_keys=True)
    return nb_expected_runs


def _main(argv=None):
    options = _get_parser2().parse_args(argv)
    get_info(**vars(options))


if __name__ == '__main__':
    _main(sys.argv[1:])
