"""Explicit file conversion for the STD-T98 debug-tool family."""
import argparse
import json
from pathlib import Path
import sys
import wave

from burst_common import bits_to_bytes, write_wav_header, samples_to_pcm


def load_codec():
    import ambe2_codec
    ambe2_codec.library()
    return ambe2_codec


def records(path, container="burst", expected=None):
    """Yield (bits, payloads); never scan for FF inside payload data."""
    with Path(path).open("rb") as stream:
        first = stream.read(2 if container == "burst" else 1)
        if not first:
            raise ValueError("Input is empty; no traffic was captured")
        if container == "burst" and (len(first) != 2 or first[0] != 255):
            raise ValueError("Expected FF burst boundary")
        bits = first[-1]
        if bits not in (49, 72) or (expected is not None and bits != expected):
            raise ValueError("Expected frame marker 31 (49 bits) or 48 (72 bits), matching the selected format")
        width, count = (bits + 7) // 8, 4 if container == "burst" else 1
        size = count * (width + 1) + (container == "burst")
        stream.seek(0)
        index = 0
        while chunk := stream.read(size):
            if len(chunk) != size:
                raise ValueError(f"Truncated {container} record {index}")
            if container == "burst" and chunk[0] != 255:
                raise ValueError(f"Invalid burst boundary at record {index}")
            start = int(container == "burst")
            payloads = []
            for phase in range(count):
                offset = start + phase * (width + 1)
                if chunk[offset] != bits:
                    raise ValueError(f"Invalid or mixed frame marker at record {index}, frame {phase}")
                payload = chunk[offset + 1:offset + 1 + width]
                if bits == 49 and payload[-1] & 127:
                    raise ValueError(f"Nonzero 49-bit padding at record {index}")
                payloads.append(payload)
            yield bits, payloads
            index += 1


def inspect_file(path, container="burst", expected=None):
    count = 0
    for bits, payloads in records(path, container, expected):
        count += len(payloads)
    return {"bits_per_frame": bits, "frames": count, "bursts": count // 4 if container == "burst" else None,
            "traffic_seconds": count * .02}


def convert(source, destination, operation="decode", container="burst", expected=None, key=None):
    # Validate the entire file before creating output or loading a native codec.
    report = inspect_file(source, container, expected)
    if operation == "fec" and report["bits_per_frame"] != 72:
        raise ValueError("FEC input must contain 72-bit frames")
    if key is not None and (container != "burst" or report["bits_per_frame"] != 49):
        raise ValueError("Legacy key application requires 49-bit .burst input")
    if key is not None and not 0 <= key <= 32767:
        raise ValueError("Key must be 0..32767")
    if Path(destination).exists():
        raise ValueError("Output exists; choose a new output path")
    decoder = None
    fec = None
    if operation == "decode":
        decoder = load_codec().AmbeDecoder()
    if operation == "fec":
        fec = load_codec().fec_demod
    if key is not None:
        from descramble import descramble_burst, generate_pn_sequence_196
        pn = generate_pn_sequence_196(key)
    with Path(destination).open("xb") as raw:
        wav = wave.open(raw, "wb") if operation == "decode" else None
        try:
            if wav:
                write_wav_header(wav)
            for bits, payloads in records(source, container, expected):
                if bits == 72 and operation == "fec":
                    converted = []
                    for payload in payloads:
                        values = list(fec(payload))
                        if len(values) != 49 or any(v not in (0, 1) for v in values):
                            raise ValueError("FEC decoder returned invalid bits")
                        converted.append(bytes(bits_to_bytes(values)))
                    payloads = converted
                if key is not None:
                    payloads = descramble_burst(payloads, pn)
                if wav:
                    for payload in payloads:
                        samples = decoder.decode_3600(payload) if bits == 72 else decoder.decode_2450(payload)
                        if len(samples) != 160:
                            raise ValueError("Vocoder must return 160 samples per 20 ms frame")
                        wav.writeframes(samples_to_pcm(samples))
                else:
                    if container == "burst":
                        raw.write(b"\xff")
                    for payload in payloads:
                        raw.write(b"\x31" + payload)
        finally:
            if wav:
                wav.close()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="STD-T98 file vocoder: explicit decode or FEC, no receiver or key search")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "decode", "fec"):
        sub = commands.add_parser(command)
        sub.add_argument("input", help=".burst file; marker specifies 72 or 49 bits")
        sub.add_argument("--container", choices=("burst", "ambe"), default="burst", help="Use ambe explicitly for legacy files without burst boundaries")
        if command != "inspect":
            sub.add_argument("-o", "--output", required=True, help="Exact output filename (never overwritten)")
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect_file(args.input, args.container)
        else:
            result = convert(args.input, args.output, args.command, args.container)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def legacy_main(operation, container, bits, with_key=False):
    parser = argparse.ArgumentParser(description="Compatibility command; see python -m std_t98_vocode --help")
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    if with_key:
        parser.add_argument("-k", "--key", required=True, type=int)
    args = parser.parse_args()
    try:
        if with_key:
            print("Key application now belongs to std-t98-cracker; this explicit-key command is retained for compatibility.", file=sys.stderr)
        result = convert(args.input, args.output, operation, container, bits, args.key if with_key else None)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
