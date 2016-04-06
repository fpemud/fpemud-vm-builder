#!/bin/bash

FILES="./fpemud-vmaker"
LIBFILES="$(find ./lib -name '*.py' | tr '\n' ' ')"
LIBFILES="${LIBFILES} $(find ./plugins -name '*.py' | tr '\n' ' ')"

autopep8 -ia --ignore=E501,E402 ${FILES}
autopep8 -ia --ignore=E501 ${LIBFILES}
