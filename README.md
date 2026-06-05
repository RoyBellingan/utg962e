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
.venv/bin/python utg900e_cli.py query ":CHANnel1:BASE:WAVe?"
```

## Python API

```python
from utg900e import UTG900E

with UTG900E() as gen:
    print(gen.identify())
    print(gen.get_settings())
    gen.set_amplitude(2.0, channel=1)
```

## SCPI reference

| Action | Command |
|--------|---------|
| Identify | `*IDN?` |
| Read amplitude | `:CHANnel1:BASE:AMPLitude?` |
| Set amplitude | `:CHANnel1:BASE:AMPLitude 2` |
| Waveform type | `:CHANnel1:BASE:WAVe?` |
| Frequency | `:CHANnel1:BASE:FREQuency?` |
| Output on/off | `:CHANnel1:OUTPut?` |

Amplitude unit defaults to Vpp; query with `:CHANnel1:AMPLitude:UNIT?`.

Full manual: [UTG900E Programming Manual (PDF)](https://unitrend.oss-cn-hongkong.aliyuncs.com/uploads/attach/20250624/101001b7758ad4009842411c05529.pdf)

## Notes

- Commands must end with newline (`\n`).
- There is no single "download all settings" command; `dump` queries each parameter individually.
- USB IDs for this unit: vendor `1a00`, product `0834`, serial `AWG1523500291`.
