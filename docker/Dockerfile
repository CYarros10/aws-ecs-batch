FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
        software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    python3.7 \
    python3-pip
RUN python3.7 -m pip install pip
RUN pip3 install awscli boto3
RUN pip3 install requests

ADD process_message.py /

CMD ["python3", "/process_message.py"]
