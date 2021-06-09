# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""Utilities for biosignal data structure."""

import os
from pathlib import Path
# from pandas import DataFrame.to_csv - .to_csv is an attribute of dataframe
import neurokit2 as nk
from pandas import Series
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import glob

sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (20.0, 12.0)
plt.rcParams.update({'font.size': 16})


def volume_counter(root, subject, ses=None, save_path=None):
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
    save_path: path
        root directory of
    Returns:
    --------
    ses_runs: dictionary
        each key lists the number of volumes in each run, including invalids
    """
    # Check directory
    if os.path.exists(root) is False:
        raise ValueError("Couldn't find the following directory: ",  root)
    # handle no save_path given
    if save_path is None:
        save_path = root
    # Check directory
    elif os.path.exists(save_path) is False:
        raise ValueError("Couldn't find the following directory: ", save_path)

    # List the files that have to be counted
    dirs = list_sub(root, subject, ses)
    ses_runs = {}
    # loop iterating through files in each dict key representing session
    # returned by list_sub
    # for this loop, exp refers to session's name,
    # avoiding confusion with ses argument
    for exp in dirs:
        for file in dirs[exp]:
            # reading acq
            bio_df, fs = nk.read_acqknowledge(os.path.join(
                                       root, subject, exp, file))  # resampling

            # initialize a df with TTL values over 4 (switch either ~0 or ~5)
            query_df = bio_df.query('TTL > 4')

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

            # saving the dataframe under specified dir and file name
            # deal with unexisting paths
            if os.path.exists(f"{save_path}{subject}") is False:
                os.mkdir(Path(f"{save_path}{subject}"))

            if os.path.exists(f"{save_path}{subject}/{exp}") is False:
                os.mkdir(Path(f"{save_path}{subject}/{exp}"))

            # Create tuples with the given indexes
            # First block is always from first trigger to first parse
            block1 = (start, parse_list[0][0])

            # runs is a list of tuples specifying runs in the session
            runs = []
            # push the resulting tuples (run_start, run_end)
            runs += [block1]
            for i in range(0, len(parse_list)-1):
                if i == len(parse_list):
                    runs += (parse_list[i][1], end)
                    break
                else:
                    runs += (parse_list[i][1], parse_list[1+i][0])
            # compute the number of trigger/volumes in the run
            for i, elem in enumerate(runs):
                runs[i] = (elem[1]-elem[0]/fs)/1.49

            ses_runs[exp] = runs

def batch_parse(root, subject, ses=None, save_path=None):
    """
    Automated signal parsing for biopac recordings following BIDS format.

    Make sure the trigger channel is named "TTL" because it is hard-coded
    Parameters:
    ------------
    root : path
        main directory containing the biopac data (e.g. /home/user/dataset)
    subject : string
        name of path for a specific subject (e.g.'sub-03')
    ses : string
        name of acquisition session. Optional workflow for specific experiment
        default is None
    save_path: path
        root directory of
    Returns:
    --------
    dirs : dict
        list_sub dictionary
    """
    # Check directory
    if os.path.exists(root) is False:
        raise ValueError("Couldn't find the following directory: ",  root)
    # handle no save_path given
    if save_path is None:
        save_path = root
    # Check directory
    elif os.path.exists(save_path) is False:
        raise ValueError("Couldn't find the following directory: ", save_path)

    # List the files that have to be parsed
    dirs = list_sub(root, subject, ses)
    # loop iterating through files in each dict key representing session
    # returned by list_sub
    # for this loop, exp refers to session's name,
    # avoiding confusion with ses argument

    for exp in dirs:
        for file in dirs[exp]:
            # reading acq, resampling at 1000Hz
            bio_df, fs = nk.read_acqknowledge(os.path.join(
                                       root, subject, exp, file))  # resampling

            # initialize a df with TTL values over 4 (switch either ~0 or ~5)
            query_df = bio_df.query('TTL > 4')

            # Define session length - this list will be less
            # memory expensive to play with than dataframe
            session = list(query_df.index)

            # maximal TR - the time (2s) distance between two adjacent TTL
            tr_period = fs * 2

            # Define session length and adjust with padding
            padding = fs * 9
            start = int(session[0]-padding)
            end = int(session[-1]+padding)

            parse_list = []

            # ascertain that session is longer than 3 min

            for idx in range(1, len(session)):
                # define time diff between current successive trigger
                time_delta = session[idx] - session[idx-1]

                # if the time diff between two trigger values over 4
                # is larger than TR, keep both indexes
                if time_delta > tr_period:
                    parse_start = int(session[idx-1] + padding)
                    parse_end = int(session[idx] - padding)
                    # adjust the segmentation with padding
                    # parse start is end of run
                    parse_list += [(parse_start, parse_end)]

            # saving the dataframe under specified dir and file name
            # deal with unexisting paths
            if os.path.exists(f"{save_path}{subject}") is False:
                os.mkdir(Path(f"{save_path}{subject}"))

            if os.path.exists(f"{save_path}{subject}/{exp}") is False:
                os.mkdir(Path(f"{save_path}{subject}/{exp}"))

            # Parse  with the given indexes
            # Keep the first segment before scanner is turned on
            # then, first block is always from first trigger to first parse
            block0 = bio_df[:start]
            block1 = bio_df[start:parse_list[0][0]]

            # runs are runs in the session
            runs = []
            # push the resulting parsed dataframes in a list
            runs += [block1]
            for i in range(0, len(parse_list)-1):
                if i == len(parse_list):
                    runs += ([bio_df[parse_list[i][1]:end]])
                    break
                else:
                    runs += ([bio_df[parse_list[i][1]:parse_list[1+i][0]]])

            sep = '_'
            name0 = sep.join([subject, exp, "prep-before-scan"])
            block0.plot(title=name0).get_figure().savefig(
                                                     f"{save_path}{subject}/"
                                                     f"{exp}/{name0}")

            # changing channel names
            for idx, run in enumerate(runs):

                run = run.rename(columns={"PPG100C": 'PPG',
                                          "Custom, HLT100C - A 6": 'RSP',
                                          "GSR-EDA100C-MRI": 'EDA',
                                          "ECG100C": 'ECG',
                                          "TTL": "TRIGGER"})

                volumes = run.query('TRIGGER > 4').iloc[-1] - run.query('TRIGGER > 4').iloc[0]
                # joining path and file name with readable Run index(01 to 0n)
                sep = '_'
                name = sep.join([subject, exp, f'task-run{idx+1:02}'])



                # write HDF5
                run.to_hdf(f"{save_path}{subject}/"
                           f"{exp}/{name}.h5", key='bio_df')
                Series(fs).to_hdf(f"{save_path}{subject}/"
                                  f"{exp}/{name}.h5", key='sampling_rate')
                Series(volumes).to_hdf(f"{save_path}{subject}/"
                                        f"{exp}/{name}.h5", key='volumes')

                # plot the run and save it
                run.plot(title=name).get_figure().savefig(
                                    f"{save_path}{subject}/{exp}/{name}")

                # notify user
                print(name, 'in file ', file,
                      'in experiment:', exp, 'is parsed.','\n'
                      ' and saved at', save_path, '| sampling rate is :', fs,
                      '~'*30)

    return dirs


def list_sub(root=None, sub=None, ses=None, type='.acq', show=False):
    """
    List a subject's files.

    Returns a dictionary entry for each session in a subject's directory
    Each entry is a list of files for a given subject/ses directory
    if ses is given, only one dictionary entry is returned

    Arguments
    ---------
    root : str path
        root directory of dataset, like "home/user/dataset"
    sub : str BIDS code
        subject number, like "sub-01"
    ses : str BIDS code
        session name or number, like "ses-001"
    type : str
        what file are we looking for. Default is biosignals from biopac
    show : bool
        Defaults to False. Else, prints the output dict
    Returns
    -------
    ses_list :
        list of sessions in the subject's folder
    files_list :
        list of files by their name

    Example :
    >>> ses_runs = list_sub(root = "/home/user/dataset", sub = "sub-01")
    """
    # Check the subject's
    #if os.path.exists(os.path.join(root, sub)) is False:
     #   raise ValueError("Couldn't find the subject's path \n",
      #                   os.path.join(root, sub))
    file_list = []
    ses_runs = {}
    ses_list = os.listdir(os.path.join(root, sub))


    # list files in only one session
    if ses is not None:
        dir = os.path.join(root, sub, ses)

        # if the path exists, list .acq files
        if os.path.exists(dir):
            for filename in os.listdir(dir):

                if filename.endswith(type):
                    file_list += [filename]
            if show:
                print("list of sessions in subjet's directory: ", ses_list)
                print('list of files in the session:', file_list)

            # return a dictionary entry for the specified session
            files = {str(ses): file_list}
            return files
        else:
            print("list of sessions in subjet's directory: ", ses_list)
            raise Exception("Session path you gave does not exist")

    # list files in all sessions (or here, exp for experiments)
    elif os.path.isdir(os.path.join(root, sub, ses_list[0])) is True:
        for exp in ses_list:
            # re-initialize the list
            file_list = []
            # iterate through directory's content
            for filename in os.listdir(os.path.join(root, sub, exp)):
                if filename.endswith(type):
                    file_list += [filename]


            # save the file_list as dict item
            ses_runs[exp] = file_list

        # display the lists (optional)
        if show:
            for exp in ses_runs:
                print(f"list of files for session {exp}: {ses_runs[exp]}")
        return ses_runs
    # list files in a sub directory without sessions
    else:
        # push filenames in a list
        for filename in os.listdir(os.path.join(root, sub)):
            if filename.endswith(type):
                file_list += [filename]
        # store list
        ses_runs['random_files'] = file_list


        # return a dictionary of sessions each containing a list of files
        return ses_runs

def batch_processing(data_path, sub):
    """
    """

    ls = list_sub(data_path, sub, type='.h5')
    print(sub)
    all_power = pd.DataFrame()
    for ses in ls:
        print(ses)
        ls_run = glob.glob(f"{data_path}{sub}/{ses}/*task-run*.h5")

        for num, run in enumerate(ls_run):
            bio_df = pd.read_hdf(f'{run}', key='bio_df')
            fs = int(pd.read_hdf(f'{run}', key='sampling_rate'))
            time = np.arange(len(bio_df))/fs

            if len(time) == 0 or time[-1] < 400:
                continue

            if os.path.exists(f"/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}") is False:
                os.mkdir(Path(f"/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}"))

            if os.path.exists(f"/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}") is False:
                os.mkdir(Path(f"/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}"))

            # PPG
            ppg_nabian = nk.ppg_clean(bio_df['PPG'],
                                      sampling_rate=fs, method='nabian2018')
            power = nk.signal_power(ppg_nabian, frequency_band=[(1,4), (5, 8), (9, 12),
                                                                (13, 16), (17,20), (20,100)],
                                    sampling_rate=fs)

            power['file'] = run
            power['ses'] = ses

            all_power = all_power.append(power, ignore_index=True)

            plt.plot(time[100000:150000], np.array(bio_df['PPG'])[100000:150000])
            plt.plot(time[100000:150000], ppg_nabian[100000:150000])
            plt.xlabel("seconds")
            plt.ylabel("V")
            plt.title(f'{sub}_{ses}_task-run0{num+1} - PPG')
            plt.savefig(f'/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}/{sub}_{ses}_task-run0{num}-PPG.png')
            plt.close()

            # EDA
            eda_clean = nk.eda_clean(bio_df['EDA'], fs)
            plt.plot(time[100000:400000], np.array(bio_df['EDA'])[100000:400000])
            plt.plot(time[100000:400000], eda_clean[100000:400000])
            plt.xlabel("seconds")
            plt.ylabel("microSiemens")
            plt.title(f'{sub}_{ses}_task-run0{num+1} - EDA')
            plt.savefig(f'/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}/{sub}_{ses}_task-run0{num}-EDA.png')
            plt.close()


            # RSP
            rsp_clean = nk.rsp_clean(bio_df['RSP'], fs, method='khodadad2018')
            plt.plot(time[100000:300000], np.array(bio_df['RSP'])[100000:300000])
            plt.plot(time[100000:300000], rsp_clean[100000:300000])
            plt.xlabel("seconds")
            plt.ylabel("V")
            plt.title(f'{sub}_{ses}_task-run0{num+1} - RSP')
            plt.savefig(f'/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}/{sub}_{ses}_task-run0{num}-RSP.png')
            plt.close()

    all_power.to_csv(f'/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/{sub}_signals_info.csv')
    #ses_list = all_power.loc[(all_power['1.00-4.00Hz'] < 0.03) & (all_power['9.00-12.00Hz'] > 0.001) |(all_power['9.00-12.00Hz'] > 0.1)].ses.unique()

    #for ses_id in ses_list:
      # img = plt.imread(f'/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses_id}/{sub}_{ses}_task-run02-PPG.png')
       # plt.imshow(img)
