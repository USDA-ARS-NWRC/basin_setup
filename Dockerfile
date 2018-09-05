# IPW is built on a ubuntu 18.04 image
FROM ubuntu:18.04

MAINTAINER Micah Johnson <micah.johnson150@gmail.com>

# Requirements
RUN apt-get update -y\
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
	pkg-config \
        python3-dev \
        python3-pip \ 
	libnetcdf-dev \
	netcdf-bin 



# create a working directory

RUN mkdir -p /code && mkdir -p /code/basin_setup
RUN cd /code/ \
  && curl http://download.osgeo.org/gdal/2.2.3/gdal-2.2.3.tar.gz --output /code/gdal.tar.gz --silent \
  && tar -xzvf /code/gdal.tar.gz \
  && rm /code/gdal.tar.gz \
  && cd /code/gdal-2.2.3/ \
  && ./configure --with-netcdf=/usr/lib/ \
  && make \
  && make install

RUN ldconfig

# Copy over everything
COPY . /code/basin_setup/

RUN cd /code/basin_setup \
    && make install \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install setuptools wheel \
    && python3 -m pip install -r requirements.txt

####################################################
# Create a shared data volume
####################################################

VOLUME /data
WORKDIR /data
ENTRYPOINT ["basin_setup"]
CMD ["/bin/bash"]
