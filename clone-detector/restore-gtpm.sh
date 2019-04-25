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
echo "restoring gtpm indexes..."
=======
rootPATH=$(dirname $scriptPATH)
printf "\e[32m[restore-gtpm.sh] \e[0mrestoring gtpm indexes...\n"
>>>>>>> 2e73ed3bfbff4d5bbd45af8ad38e71a185fb8675
if [ -d "$rootPATH/gtpmindex" ]; then
   rm -rf $rootPATH/gtpmindex
fi
cp -r $rootPATH/backup_gtpm/gtpmindex $rootPATH/

printf "\e[32m[restore-gtpm.sh] \e[0mgtpmindex restored\n"

