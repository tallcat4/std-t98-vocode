import wave
import os
import struct
import argparse
from pyambelib import AmbeDecoder
# 2450のデコードには fec_demod は不要ですが、パッケージ構成に合わせてimport行は調整してください

def decode_burst_ambe_2450(input_filename, output_filename):
    """
    バースト形式の2450 AMBE ファイルをWAVにデコード
    
    Burst Structure (33 bytes):
      [0xFF]
      + [0x31][7bytes] (Frame 1)
      + [0x31][7bytes] (Frame 2)
      + [0x31][7bytes] (Frame 3)
      + [0x31][7bytes] (Frame 4)
    """
    # ファイルの存在確認
    if not os.path.exists(input_filename):
        print(f"エラー: {input_filename} が見つかりません。")
        return

    # デコーダのインスタンス生成
    decoder = AmbeDecoder()
    
    print(f"Decoding {input_filename} (Burst 2450 decode)...")

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
            BURST_SIZE = 1 + (FRAME_SIZE * FRAMES_PER_BURST)  # 1 + 8*4 = 33 bytes
            
            burst_count = 0
            frame_count = 0
            
            while True:
                # 1バースト分を読み込み (33 bytes)
                burst_chunk = fin.read(BURST_SIZE)
                if len(burst_chunk) != BURST_SIZE:
                    break
                
                # バーストヘッダチェック
                if burst_chunk[0:1] != BURST_HEADER:
                    print(f"Warning: Burst {burst_count} does not start with 0xFF. Sync might be lost.")
                
                # 4つのフレームを処理
                for i in range(FRAMES_PER_BURST):
                    # フレムのオフセット位置計算
                    # offset 0 = 0xFF
                    # Frame 0: offset 1
                    # Frame 1: offset 9
                    # Frame 2: offset 17
                    # Frame 3: offset 25
                    offset = 1 + (i * FRAME_SIZE)
                    
                    # フレームを読み込み
                    chunk = burst_chunk[offset : offset + FRAME_SIZE]
                    
                    # ヘッダチェック (通常 0x31)
                    if chunk[0] != 0x31:
                        pass  # 警告は不要

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
                
                burst_count += 1
                    
        print(f"完了: {input_filename} -> {output_filename} ({burst_count} bursts, {frame_count} frames)")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode 2450 bps burst format AMBE audio files to WAV")
    parser.add_argument("--input", "-i", required=True, help="Input burst format file (2450 format)")
    parser.add_argument("--output", "-o", required=True, help="Output WAV file")
    args = parser.parse_args()
    
    decode_burst_ambe_2450(args.input, args.output)
