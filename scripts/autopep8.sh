#!/bin/bash

FILES="./fpemud-vmake"
LIBFILES="$(find ./lib -name '*.py' | tr '\n' ' ')"
LIBFILES="${LIBFILES} $(find ./plugin-* -name '*.py' | tr '\n' ' ')"

autopep8 -ia --ignore=E501,E402 ${FILES}
autopep8 -ia --ignore=E501 ${LIBFILES}
