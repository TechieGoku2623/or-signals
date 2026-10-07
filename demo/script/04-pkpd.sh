#!/usr/bin/env bash
set +e
or-signals pkpd --case 'data/sample/bolus.*' --plot
exit $?
