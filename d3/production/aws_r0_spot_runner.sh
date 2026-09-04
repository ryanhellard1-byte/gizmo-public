#!/bin/bash
set -u
source /etc/d3-r0.env
cd /opt/d3/phase176/repo
RUN_ROOT=/opt/d3/phase176/r0-runs
ATT=/opt/d3/phase176/aws-phase176-attestation.json
EXE=$(/usr/bin/python3 -c "import json; print(json.load(open('$ATT'))['production_executable'])")
if [ ! -x "$EXE" ]; then
  echo "attested production executable missing or not executable: $EXE" >&2
  exit 2
fi
/usr/bin/python3 d3/production/phase176_safe_resume.py \
  --machine-attestation "$ATT" dispatch \
  --run-id "$RUN_ID" \
  --executable "$EXE" \
  --run-root "$RUN_ROOT" \
  --mpi-prefix "mpirun --allow-run-as-root -np 4" \
  --mpi-tasks 4 \
  --ic-root /opt/d3/phase176/ic-r0 \
  --max-mem-mb "$MAXMEM" \
  --time-limit-cpu 259200
rc=$?
state="$RUN_ROOT/$RUN_ID/phase175_POST.json"
status=""
if [ -f "$state" ]; then
  status=$(/usr/bin/python3 -c "import json; print(json.load(open('$state')).get('status',''))" 2>/dev/null || true)
fi
logger -t d3-r0 "run=$RUN_ID rc=$rc status=$status executable=$EXE"
if [ "$status" = "COMPLETE" ] || [ "$status" = "FAILED" ]; then
  sync
  sleep 2
  /usr/sbin/shutdown -h now || true
fi
exit $rc
