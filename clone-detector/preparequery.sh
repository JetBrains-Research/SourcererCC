#!/bin/bash

realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}
num_nodes="${1:-0}"
scriptPATH=$(realpath "$0")
<<<<<<< HEAD
rootPATH=`dirname $scriptPATH`
echo "rootpath is : $rootPATH"
=======
rootPATH=$(dirname $scriptPATH)
printf "\e[32m[preparequery.sh] \e[0mrootpath is : $rootPATH\n"
>>>>>>> 2e73ed3bfbff4d5bbd45af8ad38e71a185fb8675
for i in $(seq 1 1 $num_nodes)
do
  foldername="$rootPATH/NODE_$i/query/"
  rm -rf $foldername
  mkdir -p $foldername
  queryfile="$rootPATH/query_$i.file"
  mv $queryfile $foldername/
  cp $rootPATH/sourcerer-cc.properties "$rootPATH/NODE_"$i/
  cp $rootPATH/res/log4j2.xml "$rootPATH/NODE"_$i/
done
