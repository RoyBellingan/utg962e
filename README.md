# UTG900E USB control

Control a [UNI-T UTG900E](https://www.uni-trend.com/) function generator over USB using SCPI (USBTMC).

The device speaks standard SCPI over USB Test & Measurement Class (USBTMC). On Linux this appears as `/dev/usbtmc0`.

## One-time setup

```bash
cd /home/roy/Public/utg962e
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo ./setup-access.sh
```

`setup-access.sh` installs a udev rule so your user can open `/dev/usbtmc0` without root. If permissions stay `root root` after install, unplug and replug the USB cable once.

Verify the device:

```bash
lsusb | grep -i uni
ls -l /dev/usbtmc* /dev/utg900e
```

## CLI usage

```bash
.venv/bin/python utg900e_cli.py idn
.venv/bin/python utg900e_cli.py dump -o settings.json
.venv/bin/python utg900e_cli.py get-amplitude --channel 1
.venv/bin/python utg900e_cli.py set-amplitude 1.5 --channel 1
.venv/bin/python utg900e_cli.py get-frequency --channel 1
.venv/bin/python utg900e_cli.py set-frequency 45000 --channel 1
.venv/bin/python utg900e_cli.py get-output --channel 1
.venv/bin/python utg900e_cli.py set-output on --channel 1
.venv/bin/python utg900e_cli.py set-output off --channel 1
.venv/bin/python utg900e_cli.py get-waveform --channel 1
.venv/bin/python utg900e_cli.py set-waveform SINe --channel 1
.venv/bin/python utg900e_cli.py set-waveform NOISe --channel 1
.venv/bin/python utg900e_cli.py query ":CHANnel1:BASE:WAVe?"
.venv/bin/python utg900e_cli.py write ":CHANnel1:OUTPut OFF"
```

## Python API

```python
from utg900e import UTG900E

with UTG900E() as gen:
    print(gen.identify())
    print(gen.get_settings())
    gen.set_frequency(45000, channel=1)
    gen.set_waveform("SINe", channel=1)
    gen.set_output(True, channel=1)
```

## SCPI reference

| Action | Command |
|--------|---------|
| Identify | `*IDN?` |
| Read amplitude | `:CHANnel1:BASE:AMPLitude?` |
| Set amplitude | `:CHANnel1:BASE:AMPLitude 2` |
| Read frequency | `:CHANnel1:BASE:FREQuency?` |
| Set frequency | `:CHANnel1:BASE:FREQuency 45000` |
| Read output | `:CHANnel1:OUTPut?` |
| Set output | `:CHANnel1:OUTPut ON` / `:CHANnel1:OUTPut OFF` |
| Read waveform | `:CHANnel1:BASE:WAVe?` |
| Set waveform | `:CHANnel1:BASE:WAVe SINe` / `:CHANnel1:BASE:WAVe NOISe` |

Undocumented commands can be sent with `write` (no reply) or `query` (waits for a reply). The official UTG900E programming manual has no `BURSt` subsystem; channel mode is `CONTINUE`, `AM`, `PM`, `FM`, `FSK`, `Line`, or `Log`.

Amplitude unit defaults to Vpp; query with `:CHANnel1:AMPLitude:UNIT?`.

Full manual: [UTG900E Programming Manual (PDF)](https://unitrend.oss-cn-hongkong.aliyuncs.com/uploads/attach/20250624/101001b7758ad4009842411c05529.pdf)

## Notes

- Commands must end with newline (`\n`).
- There is no single "download all settings" command; `dump` queries each parameter individually.
- USB IDs for this unit: vendor `1a00`, product `0834`, serial `AWG1523500291`.
