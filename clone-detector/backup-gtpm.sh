#!/bin/bash
<<<<<<< HEAD
#
#
=======
>>>>>>> 2e73ed3bfbff4d5bbd45af8ad38e71a185fb8675

realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}
scriptPATH=$(realpath "$0")
<<<<<<< HEAD
rootPATH=`dirname $scriptPATH`
echo "backing up gtpm indexes..."
=======
rootPATH=$(dirname $scriptPATH)
printf "\e[32m[backup-gtpm.sh] \e[0mbacking up gtpm indexes...\n"
>>>>>>> 2e73ed3bfbff4d5bbd45af8ad38e71a185fb8675
rm -rf $rootPATH/backup_gtpm
mkdir $rootPATH/backup_gtpm
cp -r $rootPATH/gtpmindex $rootPATH/backup_gtpm

printf "\e[32m[backup-gtpm.sh] \e[0mgtpmindex backup created\n"

