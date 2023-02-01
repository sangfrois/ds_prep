# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""CLI for physio utils."""

import pprintpp
import os
import logging
from CLI import _get_parser
import sys


LGR = logging.getLogger(__name__)


def list_sub(root=None, sub=None, ses=None, type='.acq',save=False, show=False):
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
    >>> ses_runs = list_sub(root = "/home/user/dataset/", sub = "sub-01")
    """
    # Check the subject's
    if os.path.isdir(os.path.join(root, sub)) is False:
        raise ValueError("Couldn't find the subject's path \n",
                         os.path.join(root, sub))
    file_list = []
    ses_runs = {}
    ses_list = os.listdir(f'{root}{sub}')
    # list files in only one session
    if ses is not None:
        dir = f'{root}{sub}/{ses}'
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
    elif os.path.isdir(f'{root}{sub}/{ses_list[0]}') is True:
        for exp in ses_list:
            if exp.endswith('.json'):
                continue
            # re-initialize the list
            file_list = []
            # iterate through directory's content
            for filename in os.listdir(f'{root}{sub}/{exp}'):
                
                if filename.endswith(type):
                    file_list += [filename]

            # save the file_list as dict item
            ses_runs[exp] = file_list
       
        # display the lists (optional)
        if show:
               pprintpp.pprint(ses_runs)
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
    if save is not False:
        print(f'write the rest of code to save where specified:{save}')

#  Get arguments


def _main(argv=None):
    options = _get_parser().parse_args(argv)
    list_sub(**vars(options))


if __name__ == '__main__':
    _main(sys.argv[1:])
