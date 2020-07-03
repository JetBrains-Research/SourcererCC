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
mkdir -p data/input data/output

# download repositories to check
cd data/input
wget https://github.com/org1/repo1 -O org1_repo1.zip
wget https://github.com/org2/repo2 -O org2_repo2.zip
# you can download more that 2 repositories
```

## Launch plagiarism detector
**One versus all other**

```shell script
# provide absolute paths to your folders 
docker run -it --rm \
-v absolute/path/to/input:/input \
-v absolute/path/to/output:/output \
plagiate -e .java \
-m versus -f org1_repo1.zip

# `-e` specify extensions - Java/C#/C++/C languages supported
# `-f` specify list of repositories that should be compared against another repositories (not in this list)  
```

**Each one to each other**

```shell script
docker run -it --rm \
-v absolute/path/to/input:/input \
-v absolute/path/to/output:/output \
plagiate -e .java \
-m all-to-all 
```