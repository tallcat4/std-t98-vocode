import contextlib
import io
from pathlib import Path
import tempfile
import unittest
import wave

from std_t98_vocode import records, inspect_file, convert, main


class VocodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'silence.burst'
        self.record = b'\xff' + (b'\x31' + bytes.fromhex('deba0301a6e600'))*4
        self.source.write_bytes(self.record*3)

    def test_strict_structure(self):
        self.assertEqual(inspect_file(self.source)['frames'], 12)
        for data in (b'', self.record[:-1], self.record+b'\xff', b'\x00'+self.record[1:], self.record[:9]+b'\x48'+self.record[10:], self.record[:-1]+b'\x01'):
            bad = self.root / 'bad.burst'
            bad.write_bytes(data)
            with self.assertRaises(ValueError):
                list(records(bad))

    def test_real_codec_wav_and_exclusive_output(self):
        output = self.root / 'sound.wav'
        convert(self.source, output)
        with wave.open(str(output), 'rb') as wav:
            self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()), (1, 2, 8000, 12*160))
        before = output.read_bytes()
        with self.assertRaises(ValueError):
            convert(self.source, output)
        self.assertEqual(before, output.read_bytes())

    def test_legacy_ambe_and_explicit_format(self):
        ambe = self.root / 'silence.ambe'
        ambe.write_bytes(self.record[1:])
        self.assertEqual(inspect_file(ambe, 'ambe')['frames'], 4)
        with self.assertRaises(ValueError):
            inspect_file(ambe)
        with self.assertRaises(ValueError):
            convert(self.source, self.root/'bad.wav', expected=72)

    def test_invalid_input_has_failure_exit_and_no_output(self):
        self.source.write_bytes(self.record[:-1])
        target = self.root/'out.wav'
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['decode', str(self.source), '-o', str(target)]), 1)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
