#!/usr/bin/env bash
set +e
or-signals quality --case 'data/sample/dropout.*'
exit $?
