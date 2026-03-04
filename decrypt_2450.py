import os
import argparse
from descramble import descramble_burst, generate_pn_sequence_196
from burst_common import (
    BURST_HEADER, FRAMES_PER_BURST, FRAME_HEADER_2450,
    FRAME_SIZE_2450, BURST_SIZE_2450, read_burst_payloads,
)

def decrypt_burst_file(input_filename, output_filename, key):
    """
    バースト形式の2450 AMBEファイルをスクランブル解除し、新しいバーストファイルとして出力
    """
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return

    key_196 = generate_pn_sequence_196(key)

    burst_count = 0

    with open(input_filename, 'rb') as fin, open(output_filename, 'wb') as fout:
        while True:
            burst_chunk = fin.read(BURST_SIZE_2450)
            if len(burst_chunk) != BURST_SIZE_2450:
                break

            if burst_chunk[0:1] != BURST_HEADER:
                print(f"Warning: Burst {burst_count} sync lost (Header not 0xFF).")

            payloads = read_burst_payloads(burst_chunk, FRAME_SIZE_2450)

            descrambled = descramble_burst(payloads, key_196)

            fout.write(BURST_HEADER)
            for payload in descrambled:
                fout.write(bytes([FRAME_HEADER_2450]))
                fout.write(payload)

            burst_count += 1

    print(f"Done: {input_filename} -> {output_filename} ({burst_count} bursts)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decrypt 2450 bps burst format AMBE files")
    parser.add_argument("--input", "-i", required=True, help="Input burst format file")
    parser.add_argument("--output", "-o", required=True, help="Output burst format file (decrypted)")
    parser.add_argument("-k", "--key", type=int, required=True, help="LFSR initial state (0-32767)")
    args = parser.parse_args()

    decrypt_burst_file(args.input, args.output, args.key)
