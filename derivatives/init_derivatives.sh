#!/bin/bash

# init a derivatives sub-folder as a datalad sub-dataset, optionally configure the git repo and bucket(s)
# usage: init_derivatives.sh <bids_path> <derivative_name> <git_remote>
# bids_path: the root of the BIDS database_path
# derivative_name: the name of the derivative, will results in a <bids_path>/derivatives/<derivative_name> sub-dataset
# git_remote (optional):
source ${BASH_SOURCE%/*}/../global/datalad.sh

bids_path=$1
derivative=$2
remote=$3

derivative_path=$bids_path/derivatives/$derivative
ds_name=$(basename $bids_path)


datalad create -d $bids_path $derivative_path
if [ -z "$remote" ] ; then
  # configure git remote
  datalad siblings -s origin -d $derivative_path --url $remote add

  # configure s3 bucket
  pushd $derivative_path
  bucket_name="cneuromod."${ds_name}".derivatives."$derivative
  init_remote_s3 $bucket_name
  git annex wanted $bucket_name "not metadata=distribution-restrictions=*"
  popd

  #push the derivatives to git
  datalad publish -d $derivative_path --to origin
fi
