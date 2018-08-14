# IPW is built on a ubuntu 18.04 image
FROM ubuntu:18.04

MAINTAINER Micah Johnson <micah.johnson150@gmail.com>

# Requirements
RUN apt-get update -y
RUN apt-get install -y \
        build-essential \
        curl \
	pkg-config

 

# create a working directory

RUN mkdir -p /code && mkdir -p /code/basin_setup
RUN cd /code/ \ 
	&& curl http://download.osgeo.org/gdal/2.2.3/gdal-2.2.3.tar.gz --output gdal.tar.gz --silent \ 
        && tar -xvzf gdal.tar.gz \
	&& rm gdal.tar.gz
RUN cd /code/gdal-2.2.3 \
	&& ./configure \
	&& make \
	&& make install
