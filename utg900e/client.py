"""SCPI client for UNI-T UTG900E over Linux USBTMC."""

from __future__ import annotations

import fcntl
import glob
import os
import struct
from typing import Any

VENDOR_ID = 0x6656
PRODUCT_ID = 0x0834
VENDOR_ID_SYSFS = "6656"
PRODUCT_ID_SYSFS = "0834"

# linux/usb/tmc.h — USBTMC_IOC_NR = 91
def _ioc(direction: int, number: int, size: int = 0) -> int:
    return (direction << 30) | (size << 16) | (91 << 8) | number


_USBTMC_IOCTL_CLEAR = _ioc(0, 2)
_USBTMC_IOCTL_ABORT_BULK_OUT = _ioc(0, 3)
_USBTMC_IOCTL_ABORT_BULK_IN = _ioc(0, 4)
_USBTMC_IOCTL_SET_TIMEOUT = _ioc(1, 10, 4)
_USBTMC_IOCTL_AUTO_ABORT = _ioc(1, 25, 1)


def _usb_ids_match(vendor: str | None, product: str | None) -> bool:
    if vendor is None or product is None:
        return False
    vendor_ok = vendor.lower() in {
        VENDOR_ID_SYSFS,
        f"{VENDOR_ID:04x}",
        f"0x{VENDOR_ID:04x}",
        str(VENDOR_ID),
    }
    product_ok = product.lower() in {
        PRODUCT_ID_SYSFS,
        f"{PRODUCT_ID:04x}",
        f"0x{PRODUCT_ID:04x}",
        str(PRODUCT_ID),
    }
    return vendor_ok and product_ok


class UTG900EError(RuntimeError):
    """Raised when communication with the generator fails."""


class _UsbtmcTransport:
    def __init__(self, device_path: str, timeout: float = 2.0) -> None:
        self.device_path = device_path
        self.timeout = timeout
        self._fd: int | None = None

    def open(self) -> None:
        try:
            self._fd = os.open(self.device_path, os.O_RDWR)
        except OSError as exc:
            raise UTG900EError(
                f"Cannot open {self.device_path}: {exc}. "
                "Run setup-access.sh with sudo to install udev permissions."
            ) from exc
        self._configure()

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def _configure(self) -> None:
        assert self._fd is not None
        timeout_ms = max(100, int(self.timeout * 1000))
        try:
            fcntl.ioctl(self._fd, _USBTMC_IOCTL_SET_TIMEOUT, struct.pack("I", timeout_ms))
        except OSError:
            pass
        try:
            fcntl.ioctl(self._fd, _USBTMC_IOCTL_AUTO_ABORT, struct.pack("B", 1))
        except OSError:
            pass

    def _recover(self) -> None:
        if self._fd is None:
            return
        for request in (
            _USBTMC_IOCTL_ABORT_BULK_IN,
            _USBTMC_IOCTL_ABORT_BULK_OUT,
            _USBTMC_IOCTL_CLEAR,
        ):
            try:
                fcntl.ioctl(self._fd, request)
            except OSError:
                pass

    def write(self, command: str) -> None:
        if self._fd is None:
            raise UTG900EError("Transport is not open")
        payload = command if command.endswith("\n") else f"{command}\n"
        try:
            os.write(self._fd, payload.encode("ascii"))
        except TimeoutError as exc:
            self._recover()
            raise UTG900EError(
                f"Write to {self.device_path} timed out. "
                "Unplug and replug the USB cable, then retry."
            ) from exc

    def read(self) -> str:
        if self._fd is None:
            raise UTG900EError("Transport is not open")

        # Kernel USBTMC delivers one complete DEV_DEP_MSG_IN per read.
        # This firmware does not terminate SCPI replies with '\n', so waiting
        # for a newline issues a second read that times out and wedges the bus.
        try:
            chunk = os.read(self._fd, 4096)
        except TimeoutError as exc:
            self._recover()
            raise UTG900EError(
                f"No response from {self.device_path} (timeout). "
                "Unplug and replug the USB cable if this persists."
            ) from exc

        if not chunk:
            raise UTG900EError(f"No response from {self.device_path} (timeout)")

        return chunk.decode("ascii", errors="replace").strip()


def find_device_path() -> str:
    """Locate the UTG900E USBTMC device node."""
    preferred = "/dev/utg900e"
    if os.path.exists(preferred):
        return preferred

    matches: list[str] = []
    for path in sorted(glob.glob("/dev/usbtmc*")):
        vendor, product = _read_usb_ids(path)
        if _usb_ids_match(vendor, product):
            matches.append(path)

    if matches:
        return matches[0]

    usbtmc_nodes = sorted(glob.glob("/dev/usbtmc*"))
    if len(usbtmc_nodes) == 1:
        return usbtmc_nodes[0]

    raise UTG900EError(
        "No UTG900E USBTMC device found. Is it connected and powered on?"
    )


def _read_usb_ids(device_path: str) -> tuple[str | None, str | None]:
    devpath = _read_udev_property(device_path, "DEVPATH")
    if not devpath:
        return None, None

    # /devices/.../usb1/1-2/1-2:1.0/usbmisc/usbtmc0 -> .../usb1/1-2
    usb_device = devpath.split("/usbmisc/")[0].rsplit("/", 1)[0]
    vendor = _read_text_file(f"/sys{usb_device}/idVendor")
    product = _read_text_file(f"/sys{usb_device}/idProduct")
    return vendor, product


def _read_udev_property(device_path: str, name: str) -> str | None:
    import subprocess

    try:
        output = subprocess.check_output(
            ["udevadm", "info", "-q", "property", "-n", device_path],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    prefix = f"{name}="
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return None


def _read_text_file(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="ascii") as handle:
        return handle.read().strip()


class UTG900E:
    """High-level SCPI interface for the UTG900E."""

    def __init__(self, device_path: str | None = None, timeout: float = 2.0) -> None:
        self.device_path = device_path or find_device_path()
        self.timeout = timeout
        self._transport = _UsbtmcTransport(self.device_path, timeout=timeout)

    def __enter__(self) -> "UTG900E":
        self.open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def open(self) -> None:
        self._transport.open()

    def close(self) -> None:
        self._transport.close()

    def write(self, command: str) -> None:
        self._transport.write(command)

    def query(self, command: str) -> str:
        self.write(command)
        return self._transport.read()

    def identify(self) -> str:
        return self.query("*IDN?")

    def get_amplitude(self, channel: int = 1) -> float:
        value = self.query(f":CHANnel{channel}:BASE:AMPLitude?")
        return float(value)

    def set_amplitude(self, value: float, channel: int = 1) -> None:
        self.write(f":CHANnel{channel}:BASE:AMPLitude {value}")

    def get_channel_settings(self, channel: int = 1) -> dict[str, str]:
        queries = {
            "output": f":CHANnel{channel}:OUTPut?",
            "mode": f":CHANnel{channel}:MODe?",
            "waveform": f":CHANnel{channel}:BASE:WAVe?",
            "frequency_hz": f":CHANnel{channel}:BASE:FREQuency?",
            "period_s": f":CHANnel{channel}:BASE:PERiod?",
            "amplitude": f":CHANnel{channel}:BASE:AMPLitude?",
            "amplitude_unit": f":CHANnel{channel}:AMPLitude:UNIT?",
            "offset_v": f":CHANnel{channel}:BASE:OFFSet?",
            "phase_deg": f":CHANnel{channel}:BASE:PHAse?",
            "high_level": f":CHANnel{channel}:BASE:HIGH?",
            "low_level": f":CHANnel{channel}:BASE:LOW?",
            "duty_percent": f":CHANnel{channel}:BASE:DUTY?",
            "load_ohm": f":CHANnel{channel}:LOAD?",
        }
        return {key: self.query(command) for key, command in queries.items()}

    def get_settings(self) -> dict[str, Any]:
        identity = self.identify()
        return {
            "identity": identity,
            "channel1": self.get_channel_settings(1),
            "channel2": self.get_channel_settings(2),
        }
