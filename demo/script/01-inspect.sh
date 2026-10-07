#!/usr/bin/env bash
set +e
or-signals inspect --case 'data/sample/clean.*'
exit $?
