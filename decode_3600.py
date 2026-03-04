import wave
import os
import struct
import argparse
from pyambelib import AmbeDecoder, fec_demod

def decode_output_ambe_via_fec(input_filename, output_filename):

    # ファイルの存在確認
    if not os.path.exists(input_filename):
        print(f"エラー: {input_filename} が見つかりません。")
        return

    # デコーダのインスタンス生成
    decoder = AmbeDecoder()
    
    print(f"Decoding {input_filename} (FEC demod -> 2450 decode)...")

    try:
        with open(input_filename, 'rb') as fin, wave.open(output_filename, 'wb') as fout:
            # WAV設定 (8kHz, 16bit, Mono)
            fout.setnchannels(1)
            fout.setsampwidth(2)
            fout.setframerate(8000)

            # 入力は3600形式 (1 byte Header + 9 bytes Data = 10 bytes)
            FRAME_SIZE = 10 
            frame_count = 0
            
            while True:
                chunk = fin.read(FRAME_SIZE)
                if len(chunk) != FRAME_SIZE:
                    break
                
                # ヘッダチェック (通常 0x48)
                if chunk[0] != 0x48:
                    pass

                # ペイロード部 (9バイト) を抽出
                payload = chunk[1:]
                
                # 1. FEC (Forward Error Correction) 復調を実行し、ビットストリームを取得
                bits = fec_demod(payload)
                
                # 2. ビット列をバイト列に変換（MSB first）
                bytes_from_bits = []
                for i in range(0, len(bits), 8):
                    byte_val = 0
                    for j in range(min(8, len(bits) - i)):
                        byte_val = (byte_val << 1) | bits[i + j]
                    
                    # パディング（8ビット未満の場合の左シフト処理）
                    if len(bits) - i < 8:
                        byte_val <<= (8 - (len(bits) - i))
                    bytes_from_bits.append(byte_val)
                
                # 3. 復調されたデータの先頭7バイトを抽出 (2450デコーダ用)
                payload_for_2450 = bytes(bytes_from_bits[:7])
                
                # 4. 2450デコーダで音声を合成
                samples = decoder.decode_2450(payload_for_2450)
                
                if samples:
                    # intリストをバイナリ(Little Endian short)に変換して書き込み
                    pcm_bytes = struct.pack(f'<{len(samples)}h', *samples)
                    fout.writeframes(pcm_bytes)
                    frame_count += 1
                    
        print(f"完了: {input_filename} -> {output_filename} ({frame_count} frames)")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode 3600 bps AMBE audio files to WAV using FEC demodulation")
    parser.add_argument("--input", "-i", required=True, help="Input AMBE file (3600 format)")
    parser.add_argument("--output", "-o", required=True, help="Output WAV file")
    args = parser.parse_args()
    
    decode_output_ambe_via_fec(args.input, args.output)