# Physio signals preparation

1. List any files in a specific subject directory in the BIDS dataset
2. Fetch recordings info (i.e. number of volumes acquired in all sessions, number of recorded functional MRI triggers in physiological recording, and name of tasks in the sessions)
3. Segment continuously recorded physiological recordings in order to match functional MRI acquistions
4. Convert segments to BIDS
5. Rename segments and discard useless ones (co-register with bold files using task names)

## 1. List physio sourcedata in the BIDS dataset
Find a CLI under `./utils/list_sub.py`. Usage can be explored through this command:

``python ./utils/list_sub.py -h``

Output looks like that :
```
{
    'ses-001': [],
    'ses-002': [
        'neuromod_video52019-12-16T16_16_10.acq',
        'neuromod_video52019-12-16T14_33_14.acq',
}
```

The function returns a dictionary organized by sessions numbers (e.g. 'ses-001'), or a list of random files if the folder is not organized into sessions

**Required arguments** :
```
-indir /path/to/bids/sourcedata/
-sub sub-01

```
Decide if you want a specific session with `-ses`
Decide if you want to print the dictionary in the command line with `-show`
The default file type to list is .acq but you can list other types with `-type`

**Optional arguments** :
```
-ses ses-011
-show True
-type '.acq'
```

## 2. Fetch dataset recordings information for a specific subject
Find another CLI under `./utils/get_info.py`. This uses the previous function in order to list all file in a subject's directory and report information. Usage can be explored through this command :

``python ./utils/get_info.py -h``




**Required arguments** :
```
-indir /path/to/bids/sourcedata/
-sub sub-01
```
Specify if you want to count the number of triggers in the physiological recording file

Decide if you want a specific sessioni with `-ses`

Decide if you want to print the dictionary in the command line with `-show`

You can save (or not) the dictionary output where you want with `-save`

**Optional arguments** :
```
-ses ses-011
-show True
-save path/to/save-data
```
#### Example
``python ds_prep/physio/utils/get_info.py -indir /data/neuromod/DATA/cneuromod/friends/sourcedata/physio/ -sub sub-01 -ses ses-029 -save /scratch/flesp/physio_data/friends/``

Output looks like that :
```
'ses-029': {
        '01': 497,
        '02': 497,
        '03': 503,
        '04': 503,
        '05': 441,
        '06': 441,
        'expected_runs': 6,
        'in_file': ['neuromod_video52020-11-30T09_03_07.acq'],
        'processed_runs': 6,
        'recorded_triggers': {'run-01': [3, 497, 497, 503, 503, 441, 441]},
        'task': [
            'task-s04e07a',
            'task-s04e07b',
            'task-s04e08a',
            'task-s04e08b',
            'task-s04e09a',
            'task-s04e09b',
        ],
    },

```

## 3. Segment continuously recorded physiological signals
Physiological recordings are continuously collected concurrent to fMRI and have to be cut accordingly. A home-brewed method was developped in order to cut these segments.

Find a function that cuts the segments and convert it to HDF5 file format under `./draft/convert_seg2hdf.py`.

***This part can be ignored as we integrated phys2bids to the preparation pipeline***

## 4. Convert segments to BIDS format
Find another CLI that cuts and converts physiological recordings using phys2bids and the dictionary returned by `get_info.py`. The previous function returns `recorded_triggers` which is the number of volumes in each fMRI acquisition. This is important for the conversion workflow as `phys2bids` uses this information to cut the acquisition segments.

*BEWARE*: Arguments taken by phys2bids such as TR, trigger channel index, and channel names are hard-coded.

**Required arguments** :
```
-indir /path/to/sourcedata/
-sub sub-01
-outdir /path/to/scratch/with-json-info
```
**Optional arguments** :
```
-ses ses-011
```
#### Example
**WATCH OUT** : make sure that the `.json` info file are in `-outdir`

``python ds_prep/physio/utils/get_info.py -indir /data/neuromod/DATA/cneuromod/friends/sourcedata/physio/ -outdir /scratch/flesp/physio_data/friends/ -sub sub-01``

## 5. Rename segments in BIDS compliant format and discard useless files
**TO-DO**
