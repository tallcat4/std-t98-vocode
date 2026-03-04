import wave
import os
import argparse
from pyambelib import AmbeDecoder
from descramble import descramble_burst, generate_pn_sequence_196
from burst_common import (
    BURST_HEADER, FRAME_SIZE_2450, BURST_SIZE_2450,
    read_burst_payloads, write_wav_header, samples_to_pcm,
)

def decode_burst_ambe_2450_descramble(input_filename, output_filename, key):
    """
    バースト形式の2450 AMBE ファイルをスクランブル解除してWAVにデコード
    """
    if not os.path.exists(input_filename):
        print(f"エラー: {input_filename} が見つかりません。")
        return

    key_196 = generate_pn_sequence_196(key)
    
    decoder = AmbeDecoder()
    
    print(f"Decoding {input_filename} (Descramble & Burst 2450 decode)...")

    try:
        with open(input_filename, 'rb') as fin, wave.open(output_filename, 'wb') as fout:
            write_wav_header(fout)

            burst_count = 0
            frame_count = 0
            
            while True:
                burst_chunk = fin.read(BURST_SIZE_2450)
                if len(burst_chunk) != BURST_SIZE_2450:
                    break
                
                if burst_chunk[0:1] != BURST_HEADER:
                    print(f"Warning: Burst {burst_count} sync lost (Header not 0xFF).")
                
                payloads = read_burst_payloads(burst_chunk, FRAME_SIZE_2450)
                
                # スクランブル解除
                descrambled = descramble_burst(payloads, key_196)
                
                # 各フレームをデコード
                for descrambled_payload in descrambled:
                    samples = decoder.decode_2450(descrambled_payload)
                    
                    if samples:
                        fout.writeframes(samples_to_pcm(samples))
                        frame_count += 1
                
                burst_count += 1
                    
        print(f"完了: {input_filename} -> {output_filename} ({burst_count} bursts processed)")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descramble and Decode 2450 bps burst format AMBE audio files")
    parser.add_argument("--input", "-i", required=True, help="Input burst format file")
    parser.add_argument("--output", "-o", required=True, help="Output WAV file")
    parser.add_argument("-k", "--key", type=int, required=True, help="LFSR initial state (0-32767)")
    args = parser.parse_args()
    
    decode_burst_ambe_2450_descramble(args.input, args.output, args.key)