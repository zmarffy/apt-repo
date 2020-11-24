FROM ubuntu

ARG DEBIAN_FRONTEND="noninteractive"
ENV TZ="America/New_York"

RUN apt-get update
RUN apt-get install gpg -y
RUN apt-get install python3 -y
RUN apt-get install reprepro -y
RUN mkdir /scripts
WORKDIR /scripts
RUN mkdir /share
RUN mkdir /debs

ARG origin
ARG label
ARG codename
ARG arch
ARG components
ARG description

ENV origin=${origin}
ENV label=${label}
ENV codename=${codename}
ENV arch=${arch}
ENV components=${components}}
ENV description=${description}

ENTRYPOINT ["python3"]
CMD ["-c", "import sys; sys.exit('ERROR: Need to run an apt-repo command')"]