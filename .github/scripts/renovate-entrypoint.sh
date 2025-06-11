#!/bin/bash

apt update

apt install -y build-essential libpq-dev

export LOG_LEVEL=debug

runuser -u ubuntu renovate --autodiscover --platform github
