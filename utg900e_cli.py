#!/usr/bin/env python3
"""CLI for UNI-T UTG900E SCPI control."""

from __future__ import annotations

import argparse
import json
import sys

from utg900e import WAVEFORMS, UTG900E, UTG900EError, normalize_waveform


def _on_off(value: str) -> bool:
    key = value.strip().lower()
    if key in {"on", "1", "true"}:
        return True
    if key in {"off", "0", "false"}:
        return False
    raise argparse.ArgumentTypeError("expected on or off")


def _waveform(value: str) -> str:
    try:
        return normalize_waveform(value)
    except UTG900EError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


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

    out_get = sub.add_parser("get-output", help="Read whether channel output is on")
    out_get.add_argument("--channel", type=int, default=1, choices=(1, 2))

    out_set = sub.add_parser("set-output", help="Enable or disable channel output")
    out_set.add_argument("state", type=_on_off, help="on or off")
    out_set.add_argument("--channel", type=int, default=1, choices=(1, 2))

    wave_get = sub.add_parser("get-waveform", help="Read channel waveform")
    wave_get.add_argument("--channel", type=int, default=1, choices=(1, 2))

    wave_set = sub.add_parser("set-waveform", help="Set channel waveform")
    wave_set.add_argument(
        "waveform",
        type=_waveform,
        help=f"Waveform name ({', '.join(WAVEFORMS)})",
    )
    wave_set.add_argument("--channel", type=int, default=1, choices=(1, 2))

    raw_q = sub.add_parser("query", help="Send a raw SCPI query and print the reply")
    raw_q.add_argument("scpi", help='SCPI query, e.g. ":CHANnel1:BASE:WAVe?"')

    raw_w = sub.add_parser("write", help="Send a raw SCPI command with no reply")
    raw_w.add_argument("scpi", help='SCPI command, e.g. ":CHANnel1:OUTPut OFF"')

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
            elif args.command == "get-output":
                print("on" if inst.get_output(args.channel) else "off")
            elif args.command == "set-output":
                inst.set_output(args.state, channel=args.channel)
                print("on" if inst.get_output(args.channel) else "off")
            elif args.command == "get-waveform":
                print(inst.get_waveform(args.channel))
            elif args.command == "set-waveform":
                inst.set_waveform(args.waveform, channel=args.channel)
                print(inst.get_waveform(args.channel))
            elif args.command == "query":
                print(inst.query(args.scpi))
            elif args.command == "write":
                inst.write(args.scpi)
    except UTG900EError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
