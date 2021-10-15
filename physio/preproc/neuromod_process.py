# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
Neuromod processing utilities
"""
# dependencies
import pandas as pd
# high-level processing utils
from neurokit2 import eda_process, rsp_process, ecg_peaks,  ppg_findpeaks
from systole.correction import correct_rr
# signal utils
from systole.utils import input_conversion
from neurokit2.misc import as_vector, intervals_to_peaks
from neurokit2 import signal_rate, signal_fixpeaks, signal_detrend
from neurokit2.signal.signal_formatpeaks import _signal_from_indices
# home brewed cleaning utils
from neuromod_clean import neuromod_ecg_clean


def neuromod_bio_process(tsv=None, h5=None, df=None, sampling_rate=10000):
    """
    Process biosignals.

    tsv :
        directory of BIDSified biosignal recording
    df (optional) :
        pandas DataFrame object
    """
    #if df and tsv and h5 is None:
        #raise ValueError("You have to give at least one of the two \n"
            #             "parameters: tsv or df")

    if tsv is not None:
        df = pd.read_csv(tsv, sep='\t', compression='gzip')

    if h5 is not None:
        df = pd.read_hdf(h5, key='bio_df')
        sampling_rate = pd.read_hdf(h5, key='sampling_rate')
    # initialize returned objects
    if df is not None:

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
       # ecg, ecg_info = neuromod_ecg_process(ecg_raw, sampling_rate=sampling_rate)
        #bio_info.update(ecg_info)
        bio_df = pd.concat([bio_df, ecg_raw], axis=1)

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
    ppg_signal = as_vector(ppg_raw)

    # Clean signal
    ppg_cleaned = signal_detrend(ppg_signal, order=1)

    # Find peaks
    info = ppg_findpeaks(ppg_cleaned, sampling_rate=sampling_rate)
    info['sampling_rate'] = sampling_rate  # Add sampling rate in dict info
    
    rr = input_conversion(info['PPG_Peaks'], input_type='peaks_idx', output_type='rr_ms', sfreq=sampling_rate)
    
    # correct beat detection
    corrected = correct_rr(rr)
    # sanitize info dict
    info['PPG_Peaks_corrected'] = input_conversion(corrected['clean_rr'],
                                                   input_type='rr_ms',
                                                   output_type='peaks_idx')
    
    info.update({'ectopic': corrected['ectopic'], 'short': corrected['short'], 'clean_rr': corrected['clean_rr'],
                 'long': corrected['long'], 'extra': corrected['extra'], 'missed': corrected['missed']})
    

    # Prepare output
    signals = pd.DataFrame(
        {"PPG_Raw": ppg_signal, "PPG_Clean": ppg_cleaned}
    )

    return signals, info

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
