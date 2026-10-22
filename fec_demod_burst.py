"""Legacy command; shared strict implementation is in std_t98_vocode."""
from std_t98_vocode import convert, legacy_main


def convert_burst_3600_to_2450(input_filename, output_filename):
    return convert(input_filename, output_filename, 'fec', 'burst', 72)


if __name__ == "__main__":
    raise SystemExit(legacy_main('fec', 'burst', 72, False))
