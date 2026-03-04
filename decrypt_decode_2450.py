import wave
import os
import struct
import argparse
from pyambelib import AmbeDecoder
from descramble import descramble_burst, generate_pn_sequence_196

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
            # WAV設定 (8kHz, 16bit, Mono)
            fout.setnchannels(1)
            fout.setsampwidth(2)
            fout.setframerate(8000)

            # バースト形式定数
            BURST_HEADER = b'\xFF'
            FRAME_SIZE = 8  # 1 byte Header(0x31) + 7 bytes Data
            FRAMES_PER_BURST = 4
            BURST_SIZE = 1 + (FRAME_SIZE * FRAMES_PER_BURST)  # 33 bytes
            
            burst_count = 0
            frame_count = 0
            
            while True:
                burst_chunk = fin.read(BURST_SIZE)
                if len(burst_chunk) != BURST_SIZE:
                    break
                
                if burst_chunk[0:1] != BURST_HEADER:
                    print(f"Warning: Burst {burst_count} sync lost (Header not 0xFF).")
                
                # 4フレーム分のペイロードを抽出
                payloads = []
                for i in range(FRAMES_PER_BURST):
                    offset = 1 + (i * FRAME_SIZE)
                    payloads.append(burst_chunk[offset + 1 : offset + FRAME_SIZE])
                
                # スクランブル解除
                descrambled = descramble_burst(payloads, key_196)
                
                # 各フレームをデコード
                for descrambled_payload in descrambled:
                    samples = decoder.decode_2450(descrambled_payload)
                    
                    if samples:
                        pcm_bytes = struct.pack(f'<{len(samples)}h', *samples)
                        fout.writeframes(pcm_bytes)
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