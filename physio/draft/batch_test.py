import neurokit2 as nk
import seaborn as sns
import matplotlib.pyplot as plt
from utils import list_sub
import pandas as pd
import numpy as np
import os
import glob

sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (20.0, 12.0)
plt.rcParams.update({'font.size': 16})


def batch_processing(data_path, sub):
    """
    """

    ls = list_sub(data_path, sub, type='.h5')
    print(sub)
    for ses in ls:
        print(ses)
        ls_run = glob.glob(f"{data_path}{sub}/{ses}/*task-run*.h5")

        for num, run in enumerate(ls_run):
            bio_df = pd.read_hdf(f'{run}', key='bio_df')
            fs = int(pd.read_hdf(f'{run}', key='sampling_rate'))
            time = np.arange(len(bio_df))/fs
            time[-1] > 400


            ppg_nabian = nk.ppg_clean(bio_df['PPG'],
                                      sampling_rate=fs, method='nabian2018')
            power = nk.signal_power(ppg_nabian, frequency_band=[(1,4), (5, 8), (9, 12),
                                                                (13, 16), (17,20), (20,100)],
                                    sampling_rate=fs)
            power['file'] = run
            power.to_hdf('/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/signals_info.h5', key='PPG-power', mode='r+')

            if os.path.exists(f"/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}") is False:
                os.mkdir(Path(f"/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}"))

            if os.path.exists(f"/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}") is False:
                os.mkdir(Path(f"/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}"))

            plt.plot(time[100000:150000], np.array(bio_df['PPG'])[100000:150000])
            plt.plot(time[100000:150000], ppg_nabian[100000:150000])
            plt.xlabel("seconds")
            plt.ylabel("V")
            plt.title(f'{sub}_{ses}_task-run0{num+1} - PPG')
            plt.savefig(f'/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}/{sub}_{ses}_task-run0{num}-PPG.png')
            plt.close()

            rsp_clean = nk.rsp_clean(bio_df['RSP'], fs, method='khodadad2018')
            plt.plot(time[100000:300000], np.array(bio_df['RSP'])[100000:300000])
            plt.plot(time[100000:300000], rsp_clean[100000:300000])
            plt.xlabel("seconds")
            plt.ylabel("V")
            plt.title(f'{sub}_{ses}_task-run0{num+1} - RSP')
            plt.savefig(f'/home/francois.lespinasse/git/movie10_phys-ds_prep/reports/figures/{sub}/{ses}/{sub}_{ses}_task-run0{num}-RSP.png')
            plt.close()
