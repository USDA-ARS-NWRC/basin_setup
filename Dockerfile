# Basin Setup requires GDAL
FROM geographica/gdal2:2.3.2

MAINTAINER Micah Johnson <micah.johnson150@gmail.com>


RUN apt-get install -y python3-pip 


# Copy over everything
RUN mkdir -p /code \
    && mkdir -p /code/basin_setup

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
