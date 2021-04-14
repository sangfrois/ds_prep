# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
Neuromod processing utilities
"""

import pandas as pd
from neurokit2 import eda_process, rsp_process
from neurokit2 import signal_rate
from neuromod_clean import neuromod_ppg_clean


def neuromod_bio_process(tsv=None, h5=None, df=None, sampling_rate=10000):
    """
    Process biosignals.

    tsv :
        directory of BIDSified biosignal recording
    df (optional) :
        pandas DataFrame object
    """
    if df and tsv and h5 is None:
        raise ValueError("You have to give at least one of the two \n"
                         "parameters: tsv or df")

    if tsv is not None:
        df = read_csv(tsv, sep='t', compression='gz')

    if h5 is not None:
        df = read_hdf(h5, key='bio_df')
        sampling_rate = read_hdf(h5, key='sampling_rate')
    # initialize returned objects
    bio_info = {}
    bio_df = pd.DataFrame()

    # initialize each signals
    ppg_raw = df["PPG"]
    rsp_raw = df["RSP"]
    eda_raw = df["EDA"]
    ecg_raw = df["ECG"]

    # ppg
    ppg, ppg_info = neuromod_ppg_process(ppg_raw, sampling_rate=sample_rate)
    bio_info.update(ppg_info)
    bio_df = pd.concat([bio_df, ppg], axis=1)

    # ecg
    ecg, ecg_info = neuromod_ecg_process(ecg_raw, sampling_rate=sample_rate)
    bio_info.update(ecg_info)
    bio_df = pd.concat([bio_df, ecg], axis=1)

    #  rsp
    rsp, rsp_info = rsp_process(rsp_raw, sampling_rate=sample_rate,
                                method='khodadad2018')
    bio_info.update(rsp_info)
    bio_df = pd.concat([bio_df, rsp], axis=1)

    #  eda
    eda, eda_info = eda_process(eda_raw, sample_rate, method='neurokit')
    bio_info.update(eda_info)
    bio_df = pd.concat([bio_df, eda], axis=1)

    # return a dataframe
    bio_df['TTL'] = df['TTL']

    return(bio_df, bio_info)


def neuromod_ppg_process(ppg_raw, sampling_rate=10000):

    ppg_clean = neuromod_ppg_clean(ppg_raw, sampling_rate=sampling_rate)

    info = ppg_findpeaks(ppg_clean, sampling_rate=sampling_rate, show=True)

    return pd.DataFrame({'PPG_Raw': ppg_raw,
                         'PPG_Clean': ppg_clean}), info
