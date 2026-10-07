#!/usr/bin/env bash
set +e
or-signals quality --case 'data/sample/artifact.*' --report --summary
exit $?
