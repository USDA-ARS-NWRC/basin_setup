#!/bin/bash
docker-compose -f docker-compose.yml run -u $(id -u) make $@
