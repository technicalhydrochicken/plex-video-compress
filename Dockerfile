FROM ubuntu:19.04

COPY requirements.txt /

RUN apt -y update && \
    apt -y install software-properties-common && \
    add-apt-repository -y ppa:stebbins/handbrake-releases && \
    apt -y update && \
    apt -y install handbrake-cli python3-pip ffmpeg && \
    pip3 install -r /requirements.txt && \
    mkdir /scan && \
    rm -rf /var/lib/apt/lists/*

VOLUME /scan

COPY compress.py /
RUN chmod 755 compress.py

ENTRYPOINT ["/compress.py", "/scan"]
