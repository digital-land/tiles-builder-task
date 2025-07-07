FROM ubuntu:20.04

RUN apt-get update \
    && apt-get install -y build-essential git libsqlite3-dev zlib1g-dev python3 curl unzip bc \
    && apt-get install -y python3-pip \
    && apt-get clean

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip -q awscliv2.zip \
    && ./aws/install --update

RUN git clone https://github.com/mapbox/tippecanoe.git \
    && cd tippecanoe \
    && make -j \
    && make install

COPY ./build.sh .

CMD ["bash", "build.sh"]
