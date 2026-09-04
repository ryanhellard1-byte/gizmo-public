#!/bin/bash
set -u
source /etc/d3-r0.env
RUN_DIR=/opt/d3/phase176/r0-runs/$RUN_ID
while true; do
  token=$(curl -fsS -m 2 -X PUT -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" http://169.254.169.254/latest/api/token 2>/dev/null || true)
  if [ -n "$token" ] && curl -fsS -m 2 -H "X-aws-ec2-metadata-token: $token" http://169.254.169.254/latest/meta-data/spot/instance-action >/tmp/d3-spot-action 2>/dev/null; then
    logger -t d3-r0 "Spot interruption for $RUN_ID; requesting native GIZMO checkpoint"
    if [ -d "$RUN_DIR" ]; then touch "$RUN_DIR/stop"; fi
    exit 0
  fi
  sleep 5
done
