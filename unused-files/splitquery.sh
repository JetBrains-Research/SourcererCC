#!/bin/bash

# Configuration stuff
<<<<<<< HEAD:clone-detector/splitquery.sh

=======
>>>>>>> 2e73ed3bfbff4d5bbd45af8ad38e71a185fb8675:unused-files/splitquery.sh
realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}
scriptPATH=$(realpath "$0")
<<<<<<< HEAD:clone-detector/splitquery.sh
rootPATH=`dirname $scriptPATH`
echo "inside splitquery "
=======
rootPATH=$(dirname $scriptPATH)
>>>>>>> 2e73ed3bfbff4d5bbd45af8ad38e71a185fb8675:unused-files/splitquery.sh
queryfile="$rootPATH/input/dataset/blocks.file"
num_files="${1:-2}"

# Work out lines per file.
total_lines=$(wc -l <${queryfile})
((lines_per_file = ($total_lines + $num_files - 1) / $num_files))

# Split the actual file, maintaining lines.
split -l $lines_per_file $queryfile $rootPATH/query.

# Debug information
printf "\e[32m[splitquery.sh] \e[0mTotal lines     = ${total_lines}\n"
printf "\e[32m[splitquery.sh] \e[0mLines  per file = ${lines_per_file}\n"    
wc -l $rootPATH/query.*
