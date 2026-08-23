#!/usr/bin/env python3
"""CLI for UNI-T UTG900E SCPI control."""

from __future__ import annotations

import argparse
import json
import sys

from utg900e import UTG900E, UTG900EError


def main() -> int:
    parser = argparse.ArgumentParser(description="Control UNI-T UTG900E over USBTMC")
    parser.add_argument(
        "--device",
        help="USBTMC device path (default: auto-detect /dev/utg900e or /dev/usbtmc*)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("idn", help="Print *IDN? response")

    dump = sub.add_parser("dump", help="Query and print current channel settings as JSON")
    dump.add_argument(
        "-o",
        "--output",
        help="Write JSON settings to this file instead of stdout",
    )

    amp_get = sub.add_parser("get-amplitude", help="Read channel amplitude")
    amp_get.add_argument("--channel", type=int, default=1, choices=(1, 2))

    amp_set = sub.add_parser("set-amplitude", help="Set channel amplitude")
    amp_set.add_argument("value", type=float, help="Amplitude in current channel unit (usually Vpp)")
    amp_set.add_argument("--channel", type=int, default=1, choices=(1, 2))

    freq_get = sub.add_parser("get-frequency", help="Read channel frequency in Hz")
    freq_get.add_argument("--channel", type=int, default=1, choices=(1, 2))

    freq_set = sub.add_parser("set-frequency", help="Set channel frequency")
    freq_set.add_argument("value", type=float, help="Frequency in Hz")
    freq_set.add_argument("--channel", type=int, default=1, choices=(1, 2))

    raw = sub.add_parser("query", help="Send a raw SCPI query")
    raw.add_argument("scpi", help='SCPI command, e.g. ":CHANnel1:BASE:WAVe?"')

    args = parser.parse_args()

    try:
        with UTG900E(device_path=args.device) as inst:
            if args.command == "idn":
                print(inst.identify())
            elif args.command == "dump":
                settings = inst.get_settings()
                payload = json.dumps(settings, indent=2, sort_keys=True)
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as handle:
                        handle.write(payload + "\n")
                    print(f"Wrote settings to {args.output}", file=sys.stderr)
                else:
                    print(payload)
            elif args.command == "get-amplitude":
                print(inst.get_amplitude(args.channel))
            elif args.command == "set-amplitude":
                inst.set_amplitude(args.value, channel=args.channel)
                print(inst.get_amplitude(args.channel))
            elif args.command == "get-frequency":
                print(inst.get_frequency(args.channel))
            elif args.command == "set-frequency":
                inst.set_frequency(args.value, channel=args.channel)
                print(inst.get_frequency(args.channel))
            elif args.command == "query":
                print(inst.query(args.scpi))
    except UTG900EError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
