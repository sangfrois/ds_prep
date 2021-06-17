# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
Neuromod processing utilities
"""
# dependencies
import pandas as pd
# high-level processing utils
from neurokit2 import eda_process, rsp_process, ecg_peaks,  ppg_findpeaks
# signal utils
from neurokit2 import signal_rate, signal_fixpeaks, signal_formatpeaks
# home brewed cleaning utils
from neuromod_clean import neuromod_ppg_clean, neuromod_ecg_clean


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
        df = pd.read_csv(tsv, sep='\t', compression='gzip')

    if h5 is not None:
        df = pd.read_hdf(h5, key='bio_df')
        sampling_rate = pd.read_hdf(h5, key='sampling_rate')
    # initialize returned objects
    bio_info = {}
    bio_df = pd.DataFrame()

    # initialize each signals
    ppg_raw = df["PPG"]
    rsp_raw = df["RSP"]
    eda_raw = df["EDA"]
    ecg_raw = df["ECG"]

    # ppg
    ppg, ppg_info = neuromod_ppg_process(ppg_raw, sampling_rate=sampling_rate)
    bio_info.update(ppg_info)
    bio_df = pd.concat([bio_df, ppg], axis=1)

    # ecg
    ecg, ecg_info = neuromod_ecg_process(ecg_raw, sampling_rate=sampling_rate)
    bio_info.update(ecg_info)
    bio_df = pd.concat([bio_df, ecg], axis=1)

    #  rsp
    rsp, rsp_info = rsp_process(rsp_raw, sampling_rate=sampling_rate,
                                method='khodadad2018')
    bio_info.update(rsp_info)
    bio_df = pd.concat([bio_df, rsp], axis=1)

    #  eda
    eda, eda_info = eda_process(eda_raw, sampling_rate, method='neurokit')
    bio_info.update(eda_info)
    bio_df = pd.concat([bio_df, eda], axis=1)

    # return a dataframe
    bio_df['TTL'] = df['TTL']

    return(bio_df, bio_info)


def neuromod_ppg_process(ppg_raw, sampling_rate=10000):
    """
    Process PPG signal.

    Custom processing function for neuromod PPG acquisition

    Parameters
    -----------
    ppg_raw : vector
        The raw PPG channel.
    sampling_rate : int
        The sampling frequency of `ppg_signal` (in Hz, i.e., samples/second).
        Defaults to 10000.
    Returns
    -------
    signals : DataFrame
        A DataFrame containing the cleaned ppg signals.
        - *"PPG_Raw"*: the raw signal.
        - *"PPG_Clean"*: the cleaned signal.
        - *"PPG_Rate"*: the heart rate as measured based on PPG peaks.
        - *"PPG_Peaks"*: the PPG peaks marked as "1" in a list of zeros.
    info : dict
        containing list of intervals between peaks
    """
    # Prepare signal for processing
    ppg_clean = neuromod_ppg_clean(ppg_raw, sampling_rate=sampling_rate)

    # Find peaks
    info = ppg_findpeaks(ppg_clean, sampling_rate=sampling_rate)

    # correct beat detection
    _, peaks = signal_fixpeaks(peaks=info,
                               sampling_rate=sampling_rate,
                               iterative=True, interval_min=0.5,
                               interval_max=1.5, method="Kubios")
    info_corrected = {"PPG_Peaks": peaks}
    # Mark peaks
    peaks_signal = signal_formatpeaks(info_corrected,
                                      desired_length=len(ppg_clean),
                                      peak_indice=info_corrected)
    # Rate computation
    rate = signal_rate(info_corrected["PPG_Peaks"],
                       sampling_rate=sampling_rate,
                       desired_length=len(ppg_clean))
    # sanitize info dict
    info_corrected["PPG_Peaks_uncorrected"] = info["PPG_Peaks"]

    return pd.DataFrame({"PPG_Raw": ppg_raw,
                         "PPG_Clean": ppg_clean,
                         "PPG_Peaks": peaks_signal,
                         "PPG_Rate": rate}), info_corrected


def neuromod_ecg_process(ecg_raw, sampling_rate=10000, method='fmri'):
    """
    Process neuromod ECG.

    Custom processing for neuromod ECG acquisition.

    Parameters
    -----------
    ecg_raw : vector
        The raw ECG channel.
    sampling_rate : int
        The sampling frequency of `ecg_signal` (in Hz, i.e., samples/second).
        Defaults to 10000.
    method : str
        The processing pipeline to apply. Defaults to 'fmri'
    Returns
    -------
    signals : DataFrame
        A DataFrame containing the cleaned ppg signals.
        - *"ECG_Raw"*: the raw signal.
        - *"ECG_Clean"*: the cleaned signal.
        - *"ECG_Rate"*: the heart rate as measured based on PPG peaks.
    info : dict
        containing list of peaks
    """
    # prepare signal for processing
    ecg_clean = neuromod_ecg_clean(ecg_raw, sampling_rate=sampling_rate,
                                   method=method)
    # Detect beats
    instant_peaks, rpeaks, = ecg_peaks(ecg_cleaned=ecg_clean,
                                       sampling_rate=sampling_rate,
                                       correct_artifacts=True)
    # Compute rate based on peaks
    rate = signal_rate(rpeaks, sampling_rate=sampling_rate,
                       desired_length=len(ecg_clean))

    return pd.DataFrame({'ECG_Raw': ecg_raw,
                         'ECG_Clean': ecg_clean,
                         'ECG_Rate': rate,
                         'ECG_Peaks': instant_peaks}), rpeaks
