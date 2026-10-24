"""ctypes adapter for ambe2-c; 49-bit files use ThumbDV, not ambe_d order."""
import ctypes as ct
from functools import lru_cache
import os
from pathlib import Path
import sys


@lru_cache(maxsize=1)
def library():
    name = "ambe2.dll" if sys.platform == "win32" else "libambe2.dylib" if sys.platform == "darwin" else "libambe2.so"
    path = Path(os.environ.get("STD_T98_AMBE2_LIBRARY", Path(__file__).resolve().parent / "build" / name)).resolve()
    if not path.is_file():
        raise ImportError(f"ambe2-c library not found: {path}; run build.ps1 / python build.py (see README)")
    lib = ct.CDLL(str(path))
    # The upstream state grew in newer revisions. Let the compiled header
    # determine its size instead of duplicating a private layout in Python.
    try:
        lib.std_t98_ambe2_decoder_size.argtypes = []
        lib.std_t98_ambe2_decoder_size.restype = ct.c_size_t
    except AttributeError as exc:
        raise ImportError('Outdated ambe2-c adapter library; rebuild with build.ps1 / python build.py') from exc
    state = ct.c_void_p
    byte = ct.POINTER(ct.c_uint8)
    pcm = ct.POINTER(ct.c_int16)
    lib.blip25_init.argtypes = [state]
    lib.blip25_init.restype = None
    lib.blip25_decode_2450_thumbdv.argtypes = [state, byte, pcm]
    lib.blip25_decode_2450_thumbdv.restype = ct.c_int
    lib.blip25_decode_3600.argtypes = [state, byte, pcm, ct.POINTER(ct.c_int)]
    lib.blip25_decode_3600.restype = ct.c_int
    lib.blip25_fec_3600.argtypes = [byte, byte, byte]
    lib.blip25_fec_3600.restype = ct.c_int
    lib.blip25_bits_to_thumbdv.argtypes = [byte, byte]
    lib.blip25_bits_to_thumbdv.restype = None
    return lib


def _frame(payload, size):
    if len(payload) != size:
        raise ValueError(f"Expected {size} bytes per AMBE frame")
    if size == 7 and payload[-1] & 127:
        raise ValueError("Nonzero 49-bit padding")
    return (ct.c_uint8 * size).from_buffer_copy(bytes(payload))


class AmbeDecoder:
    """One independent decoder state per continuous audio stream."""
    def __init__(self):
        self._lib = library()
        self._state = ct.create_string_buffer(self._lib.std_t98_ambe2_decoder_size())
        self._lib.blip25_init(ct.byref(self._state))

    def decode_2450(self, payload):
        pcm = (ct.c_int16 * 160)()
        self._lib.blip25_decode_2450_thumbdv(ct.byref(self._state), _frame(payload, 7), pcm)
        return list(pcm)

    def decode_3600(self, payload):
        # Keep native error concealment for uncorrectable channel frames.
        pcm = (ct.c_int16 * 160)()
        self._lib.blip25_decode_3600(ct.byref(self._state), _frame(payload, 9), pcm, None)
        return list(pcm)


def fec_demod(payload):
    """Return 49 bits in the existing .burst ThumbDV order (best-effort FEC)."""
    bits = (ct.c_uint8 * 49)()
    packed = (ct.c_uint8 * 7)()
    lib = library()
    lib.blip25_fec_3600(_frame(payload, 9), bits, None)
    lib.blip25_bits_to_thumbdv(bits, packed)
    return [(packed[i // 8] >> (7 - i % 8)) & 1 for i in range(49)]
