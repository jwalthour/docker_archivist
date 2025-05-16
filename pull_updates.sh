#!/bin/bash

# Run pull_updates.py.  Intended to be run as a cronjob owned by the user `librarian`.

cd /home/librarian/docker_archivist
source ./venv/bin/activate
python pull_updates.py