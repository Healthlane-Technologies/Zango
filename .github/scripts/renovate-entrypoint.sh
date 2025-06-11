#!/bin/bash

apt update

apt install -y build-essential libpq-dev

runuser -u ubuntu renovate --autodiscover
