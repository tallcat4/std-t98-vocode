import os
import argparse
from descramble import descramble_burst, generate_pn_sequence_196

def decrypt_burst_file(input_filename, output_filename, key):
    """
    バースト形式の2450 AMBEファイルをスクランブル解除し、新しいバーストファイルとして出力
    """
    if not os.path.exists(input_filename):
        print(f"エラー: {input_filename} が見つかりません。")
        return

    key_196 = generate_pn_sequence_196(key)

    BURST_HEADER = b'\xFF'
    FRAME_HEADER = 0x31
    FRAME_SIZE = 8
    FRAMES_PER_BURST = 4
    BURST_SIZE = 1 + (FRAME_SIZE * FRAMES_PER_BURST)

    burst_count = 0

    with open(input_filename, 'rb') as fin, open(output_filename, 'wb') as fout:
        while True:
            burst_chunk = fin.read(BURST_SIZE)
            if len(burst_chunk) != BURST_SIZE:
                break

            if burst_chunk[0:1] != BURST_HEADER:
                print(f"Warning: Burst {burst_count} sync lost (Header not 0xFF).")

            payloads = []
            for i in range(FRAMES_PER_BURST):
                offset = 1 + (i * FRAME_SIZE)
                payloads.append(burst_chunk[offset + 1 : offset + FRAME_SIZE])

            descrambled = descramble_burst(payloads, key_196)

            fout.write(BURST_HEADER)
            for payload in descrambled:
                fout.write(bytes([FRAME_HEADER]))
                fout.write(payload)

            burst_count += 1

    print(f"完了: {input_filename} -> {output_filename} ({burst_count} bursts)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decrypt 2450 bps burst format AMBE files")
    parser.add_argument("--input", "-i", required=True, help="Input burst format file")
    parser.add_argument("--output", "-o", required=True, help="Output burst format file (decrypted)")
    parser.add_argument("-k", "--key", type=int, required=True, help="LFSR initial state (0-32767)")
    args = parser.parse_args()

    decrypt_burst_file(args.input, args.output, args.key)
