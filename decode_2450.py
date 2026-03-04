import wave
import os
import struct
import argparse
from pyambelib import AmbeDecoder
# 2450のデコードには fec_demod は不要ですが、パッケージ構成に合わせてimport行は調整してください

def decode_output_ambe_2450(input_filename, output_filename):

    # ファイルの存在確認
    if not os.path.exists(input_filename):
        print(f"エラー: {input_filename} が見つかりません。")
        return

    # デコーダのインスタンス生成
    decoder = AmbeDecoder()
    
    print(f"Decoding {input_filename} (Direct 2450 decode)...")

    try:
        with open(input_filename, 'rb') as fin, wave.open(output_filename, 'wb') as fout:
            # WAV設定 (8kHz, 16bit, Mono)
            fout.setnchannels(1)
            fout.setsampwidth(2)
            fout.setframerate(8000)

            # 入力は2450形式 (1 byte Header + 7 bytes Data = 8 bytes)
            FRAME_SIZE = 8 
            frame_count = 0
            
            while True:
                chunk = fin.read(FRAME_SIZE)
                if len(chunk) != FRAME_SIZE:
                    break
                
                # ヘッダチェック (通常 0x31)
                if chunk[0] != 0x31:
                    pass

                # ペイロード部 (7バイト) を抽出
                payload = chunk[1:]
                
                # 2450形式ファイルはFEC処理済みのデータなので、
                # fec_demodを通さずに直接デコーダに渡します。
                samples = decoder.decode_2450(payload)
                
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
    parser = argparse.ArgumentParser(description="Decode 2450 bps AMBE audio files to WAV")
    parser.add_argument("--input", "-i", required=True, help="Input AMBE file (2450 format)")
    parser.add_argument("--output", "-o", required=True, help="Output WAV file")
    args = parser.parse_args()
    
    decode_output_ambe_2450(args.input, args.output)