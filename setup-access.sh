#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULE_SRC="$ROOT/99-uni-trend-utg900e.rules"
RULE_DST="/etc/udev/rules.d/99-uni-trend-utg900e.rules"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo $0" >&2
  exit 1
fi

install -m 644 "$RULE_SRC" "$RULE_DST"
udevadm control --reload-rules

if [[ -e /dev/usbtmc0 ]]; then
  echo "Re-applying udev rules on /dev/usbtmc0 ..."
  udevadm trigger --name-match=usbtmc0 --action=add
  udevadm settle
fi

echo "Installed $RULE_DST"
echo
echo "Check permissions:"
ls -l /dev/usbtmc* /dev/utg900e 2>/dev/null || ls -l /dev/usbtmc* 2>/dev/null || true
echo
if [[ ! -e /dev/utg900e ]] || [[ ! -r /dev/usbtmc0 ]]; then
  echo "If permissions are still root-only, unplug and replug the USB cable."
fi
