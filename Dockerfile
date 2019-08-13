# Basin Setup requires GDAL
FROM geographica/gdal2:2.3.2

MAINTAINER Micah Johnson <micah.johnson150@gmail.com>

ENV TAUDEM_HASH f927ca639a1834565a76cb3df5acbcd2909d6d0d

ADD https://github.com/dtarb/TauDEM/archive/${TAUDEM_HASH}.tar.gz .

RUN apt-get -y update && apt-get install -y mpich
RUN apt-get install -y python3-pip && apt-get autoremove

# Build taudem
RUN tar -xzf ${TAUDEM_HASH}.tar.gz -C /usr/src \
    && mkdir /usr/src/TauDEM-${TAUDEM_HASH}/bin \
    && cd /usr/src/TauDEM-${TAUDEM_HASH}/src \
    && make

RUN mkdir -p /usr/local/taudem/bin && cp /usr/src/TauDEM-${TAUDEM_HASH}/bin/* /usr/local/taudem/bin/
ENV PATH /usr/local/taudem/bin:$PATH

# Copy over everything
RUN mkdir -p /code \
    && mkdir -p /code/basin_setup

COPY . /code/basin_setup/

RUN cd /code/basin_setup \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install setuptools wheel \
    && python3 -m pip install -r requirements.txt \
    && python3 setup.py install

####################################################
# Create a shared data volume
####################################################

VOLUME /data
WORKDIR /data
RUN echo "umask 0002" >> /etc/bash.bashrc
ENTRYPOINT ["basin_setup"]
