"""Legacy command; shared strict implementation is in std_t98_vocode."""
from std_t98_vocode import convert, legacy_main


def decrypt_burst_file(input_filename, output_filename, key):
    return convert(input_filename, output_filename, 'descramble', 'burst', 49, key)


if __name__ == "__main__":
    raise SystemExit(legacy_main('descramble', 'burst', 49, True))
