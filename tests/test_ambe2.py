"""Check the Python/container boundary against ambe2-c's unmodified CLI."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import wave

from ambe2_codec import AmbeDecoder, fec_demod
from burst_common import bits_to_bytes
from std_t98_vocode import convert, records

ROOT = Path(__file__).resolve().parents[1]


def pcm(path):
    with wave.open(str(path), "rb") as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 8000)
        return w.readframes(w.getnframes())


class Ambe2Tests(unittest.TestCase):
    def test_native_cli_equivalence_and_stream_reset(self):
        oracle = ROOT / "build" / ("ambe2wav.exe" if sys.platform == "win32" else "ambe2wav")
        vectors = ROOT / "ambe2-c-source/decoder/tests/vectors"
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            # Noisy vectors include the native error-concealment path.
            for vector in ("chip3600", "noisy3600"):
                data = (vectors / (vector + ".bin")).read_bytes()
                data = data[:len(data) // 36 * 36]
                frames72 = [data[i:i+9] for i in range(0, len(data), 9)]
                frames49 = [bytes(bits_to_bytes(fec_demod(f))) for f in frames72]
                for bits, frames in ((72, frames72), (49, frames49)):
                    native_input = tmp / "native.bin"
                    native_output = tmp / "native.wav"
                    native_input.write_bytes(b"".join(frames))
                    subprocess.run([str(oracle), str(native_input), str(native_output), "--rate", "33" if bits == 72 else "34"], check=True, capture_output=True)
                    expected = pcm(native_output)
                    for container in ("burst", "ambe"):
                        source = tmp / f"{vector}-{bits}.{container}"
                        step = 4 if container == "burst" else 1
                        source.write_bytes(b"".join((b"\xff" if step == 4 else b"") + b"".join(bytes([bits])+f for f in frames[i:i+step]) for i in range(0, len(frames), step)))
                        for repeat in range(2):
                            dest = source.with_name(source.name + f"-{repeat}.wav")
                            convert(source, dest, container=container)
                            self.assertEqual(pcm(dest), expected)
                        if bits == 72:
                            fec_output = source.with_name(source.name + "-fec")
                            convert(source, fec_output, operation="fec", container=container)
                            self.assertEqual([f for _, fs in records(fec_output, container) for f in fs], frames49)

    def test_native_boundary_validation(self):
        decoder = AmbeDecoder()
        for payload in (b"", bytes(6), bytes(8), bytes(6)+b"\x01"):
            with self.assertRaises(ValueError):
                decoder.decode_2450(payload)
        for payload in (b"", bytes(8), bytes(10)):
            with self.assertRaises(ValueError):
                decoder.decode_3600(payload)
            with self.assertRaises(ValueError):
                fec_demod(payload)


if __name__ == "__main__":
    unittest.main()
