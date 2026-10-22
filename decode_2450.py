"""Legacy command; shared strict implementation is in std_t98_vocode."""
from std_t98_vocode import convert, legacy_main


def decode_output_ambe_2450(input_filename, output_filename):
    return convert(input_filename, output_filename, 'decode', 'ambe', 49)


if __name__ == "__main__":
    raise SystemExit(legacy_main('decode', 'ambe', 49, False))
