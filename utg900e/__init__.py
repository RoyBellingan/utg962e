"""Control UNI-T UTG900E series generators over USBTMC SCPI."""

from .client import WAVEFORMS, UTG900E, UTG900EError, normalize_waveform

__all__ = ["WAVEFORMS", "UTG900E", "UTG900EError", "normalize_waveform"]
