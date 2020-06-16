# How to launch one liner for plagiarism detector

## Build docker image
```shell script
git clone https://github.com/JetBrains-Research/SourcererCC
cd SourcererCC
docker build -t  plagiate .
```

## Prepare data
```shell script
# create directories to share
mkdir -p /path/to/input/dir
mkdir -p /path/to/output/dir

# download repositories to check
cd ~/java/input
wget https://github.com/org1/repo1/archive/master.zip -O org1_repo1.zip
wget https://github.com/org2/repo2/archive/master.zip -O org2_repo2.zip
# you can download more that 2 repositories
```

## launch plagiarism detector
```shell script
docker run -it --rm -v /path/to/input/dir:/input -v /path/to/output/dir:/output \
plagiate -e .java \
-m versus -f org1_repo1.zip

# `-e` specify extensions - Java/C#/C++/C languages supported
# `-f` specify list of repositories that should be compared against another repositories (not in this list)  
```