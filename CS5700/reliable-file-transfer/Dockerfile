FROM python:3.12

RUN apt-get update
RUN apt-get install -y iproute2 iptables tcpdump net-tools iputils-ping
RUN DEBIAN_FRONTEND=noninteractive apt -y install tshark iperf3

RUN pip3 install cryptography