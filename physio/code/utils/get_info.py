# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""another util for physio CLI."""

import list_sub
import json
import logging
from CLI import _get_parser
from pandas import read_csv

LGR = logging.getLogger(__name__)


def get_info(root=None, sub=None):
    """
    List a subject's files.

    Returns a dictionary entry for each session in a subject's directory
    Each entry is a list of files for a given subject/ses directory
    if ses is given, only one dictionary entry is returned

    Arguments
    ---------
    root :
        root directory of dataset, like "home/user/dataset"
    sub :
        subject number, like "sub-01"
    ses :
        session name or number, like "ses-hcptrt1"
    type :
        what file are we looking for. Default is biosignals from biopac
    show :
        if you want to print the dictionary
    save :
        if you want to save the dictionary in json format

    Returns
    -------
    ses_list :
        list of sessions in the subject's folder
    files_list :
        list of files by their name

    Example :
    >>> ses_runs = list_sub(root = "/home/user/dataset", sub = "sub-01")
    """
    # list matches for a whole subject's dir
    ses_runs_matches = list_sub(f"{root}/sourcedata/physio", sub, type='.tsv')

    # go to fmri matches and get entries for each run of a session
    nb_expected_runs = {}
    nb_expected_volumes = {}
    # iterate through keys
    for ses in ses_runs_matches:
        df = read_csv(f"{root}/sourcedata/physio/{sub}/{ses}/{ses[0]}")
        # save number of runs
        nb_expected_runs['nb_runs'] = len(df)

        # get filename
        run_count = 1
        for filename in df.loc[:, 0]:
            with open(f"{root}/{sub}/{ses}/{filename[:-7]}.json") as f:
                bold = json.load(f)

            nb_expected_volumes[run_count] = bold["times"]["samples"]["AcquisitionNumber"][-1]
            run_count += 1
        # push number of volumes in run in dict
        nb_expected_runs[ses] = nb_expected_volumes


def _main(argv=None):
    options = _get_parser().parse_args(argv)
    get_info(**vars(options))