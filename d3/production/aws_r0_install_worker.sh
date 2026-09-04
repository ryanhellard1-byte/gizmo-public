#!/bin/bash
set -euo pipefail
if [ "$#" -ne 2 ]; then
  echo "usage: $0 RUN_ID MAXMEM_MB" >&2
  exit 2
fi
RUN_ID=$1
MAXMEM=$2
case "$RUN_ID" in
  PH165-0049|PH165-0050|PH165-0051|PH165-0052|PH165-0053|PH165-0054|PH165-0055|PH165-0056) ;;
  *) echo "refusing non-R0 run id: $RUN_ID" >&2; exit 2 ;;
esac
case "$MAXMEM" in
  ''|*[!0-9]*) echo "MAXMEM_MB must be a positive integer" >&2; exit 2 ;;
esac
if [ "$MAXMEM" -le 0 ]; then
  echo "MAXMEM_MB must be positive" >&2
  exit 2
fi
if ! command -v curl >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq curl
fi
install -m 0755 d3/production/aws_r0_spot_runner.sh /usr/local/bin/d3-r0-run.sh
install -m 0755 d3/production/aws_r0_spot_guard.sh /usr/local/bin/d3-r0-spot-guard.sh
cat > /etc/d3-r0.env <<EOF
RUN_ID=$RUN_ID
MAXMEM=$MAXMEM
EOF
chmod 0644 /etc/d3-r0.env
cat > /etc/systemd/system/d3-r0-spot-guard.service <<'EOF'
[Unit]
Description=D3 R0 Spot interruption checkpoint guard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/d3-r0-spot-guard.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/d3-r0.service <<'EOF'
[Unit]
Description=D3 R0 commissioning run
After=network-online.target d3-r0-spot-guard.service
Wants=network-online.target
Requires=d3-r0-spot-guard.service

[Service]
Type=simple
WorkingDirectory=/opt/d3/phase176/repo
ExecStart=/usr/local/bin/d3-r0-run.sh
Restart=no
TimeoutStopSec=130

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable d3-r0-spot-guard.service d3-r0.service
systemctl restart d3-r0-spot-guard.service
systemctl start d3-r0.service
printf 'D3 R0 worker installed: run_id=%s maxmem_mb=%s\n' "$RUN_ID" "$MAXMEM"
