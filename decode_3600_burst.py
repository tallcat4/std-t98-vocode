"""Legacy command; shared strict implementation is in std_t98_vocode."""
from std_t98_vocode import convert, legacy_main


def decode_burst_ambe_via_fec(input_filename, output_filename):
    return convert(input_filename, output_filename, 'decode', 'burst', 72)


if __name__ == "__main__":
    raise SystemExit(legacy_main('decode', 'burst', 72, False))
