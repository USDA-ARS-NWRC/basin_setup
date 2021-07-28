# Basin Setup requires GDAL
FROM osgeo/gdal:ubuntu-full-3.3.0

ENV TAUDEM_HASH f927ca639a1834565a76cb3df5acbcd2909d6d0d

WORKDIR /code

ADD https://github.com/dtarb/TauDEM/archive/${TAUDEM_HASH}.tar.gz .

RUN apt-get -y update \
    && apt-get install -y mpich git python3-pip libnetcdf-dev \
    && apt-get autoremove

# Build taudem
RUN tar -xzf ${TAUDEM_HASH}.tar.gz \
    && mkdir /code/TauDEM-${TAUDEM_HASH}/bin \
    && cd /code/TauDEM-${TAUDEM_HASH}/src \
    && make \
    && mkdir -p /usr/local/taudem/bin \
    && cp /code/TauDEM-${TAUDEM_HASH}/bin/* /usr/local/taudem/bin/ \
    && rm -rf /code/TauDEM-${TAUDEM_HASH}

ENV PATH /usr/local/taudem/bin:$PATH

# Copy over code base
# RUN mkdir -p /code \
#     && mkdir -p /code/basin_setup

COPY . /code/basin_setup/

RUN cd /code/basin_setup \
    && python3 -m pip install --no-cache-dir setuptools wheel \
    && python3 -m pip install --no-cache-dir -r requirements.txt \
    && python3 setup.py install \
    && rm -rf /var/lib/apt/lists/*

# Setup the shared volume and add it as the starting place
VOLUME /data
WORKDIR /data

ENTRYPOINT ["generate_topo"]
