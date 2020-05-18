FROM ubuntu:18.04

RUN apt update && apt install  -y --no-install-suggests --no-install-recommends python3-dev gcc g++ python3-pip  ant \
    openjdk-8-jdk python3-setuptools git-core && pip3 install wheel

RUN mkdir _plagiate_detector
WORKDIR /_plagiate_detector
COPY . .

RUN pip3 install -r requirements.txt && git submodule update --init && python3 -m tokenizers.parsers

RUN chmod +x main.py

ENTRYPOINT ["./main.py"]