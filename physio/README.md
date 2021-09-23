# Physio signals preparation

1. List physio sourcedata in the BIDS dataset
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
Decide if you want a specific session, or if you want to print the dictionary in the command line. 
The default file type to list is .acq but you can list other types.

**Optional arguments** :
```
-ses ses-011
-show True
-type '.acq'
```

## 2. Fetch dataset recordings information for a specific subject
Find another CLI under `./utils/get_info.py`. This uses the previous function in order to list all file in a subject's directory and report information. Usage can be explored through this command :

``python ./utils/get_info.py -h``

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


**Required arguments** :
```
-indir /path/to/bids/sourcedata/
-sub sub-01
```
Specify if you want to count the number of triggers in the physiological recording file
Decide if you want a specific session, or if you want to print the dictionary in the command line.
You can save (or not) the dictionary output where you want

**Optional arguments** :
```
-ses ses-011
-show True
-save path/to/save-data
```

