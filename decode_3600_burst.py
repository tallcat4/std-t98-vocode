import wave
import os
import struct
import argparse
from pyambelib import AmbeDecoder, fec_demod

def decode_burst_ambe_via_fec(input_filename, output_filename):
    """
    バースト形式の3600 AMBE ファイルをWAVにデコード
    
    Burst Structure (41 bytes):
      [0xFF] 
      + [0x48][9bytes] (Frame 1)
      + [0x48][9bytes] (Frame 2)
      + [0x48][9bytes] (Frame 3)
      + [0x48][9bytes] (Frame 4)
    """
    # ファイルの存在確認
    if not os.path.exists(input_filename):
        print(f"エラー: {input_filename} が見つかりません。")
        return

    # デコーダのインスタンス生成
    decoder = AmbeDecoder()
    
    print(f"Decoding {input_filename} (Burst 3600 FEC demod -> 2450 decode)...")

    try:
        with open(input_filename, 'rb') as fin, wave.open(output_filename, 'wb') as fout:
            # WAV設定 (8kHz, 16bit, Mono)
            fout.setnchannels(1)
            fout.setsampwidth(2)
            fout.setframerate(8000)

            # バースト形式定数
            BURST_HEADER = b'\xFF'
            FRAME_SIZE = 10  # 1 byte Header(0x48) + 9 bytes Data
            FRAMES_PER_BURST = 4
            BURST_SIZE = 1 + (FRAME_SIZE * FRAMES_PER_BURST)  # 1 + 10*4 = 41 bytes
            
            burst_count = 0
            frame_count = 0
            
            while True:
                # 1バースト分を読み込み (41 bytes)
                burst_chunk = fin.read(BURST_SIZE)
                if len(burst_chunk) != BURST_SIZE:
                    break
                
                # バーストヘッダチェック
                if burst_chunk[0:1] != BURST_HEADER:
                    print(f"Warning: Burst {burst_count} does not start with 0xFF. Sync might be lost.")
                
                # 4つのフレームを処理
                for i in range(FRAMES_PER_BURST):
                    # フレームのオフセット位置計算
                    # offset 0 = 0xFF
                    # Frame 0: offset 1
                    # Frame 1: offset 11
                    # Frame 2: offset 21
                    # Frame 3: offset 31
                    offset = 1 + (i * FRAME_SIZE)
                    
                    # フレームを読み込み
                    chunk = burst_chunk[offset : offset + FRAME_SIZE]
                    
                    # ヘッダチェック (通常 0x48)
                    if chunk[0] != 0x48:
                        pass  # 警告は不要

                    # ペイロード部 (9バイト) を抽出
                    payload = chunk[1:]
                    
                    # 1. FEC (Forward Error Correction) 復調を実行し、ビットストリームを取得
                    bits = fec_demod(payload)
                    
                    # 2. ビット列をバイト列に変換（MSB first）
                    bytes_from_bits = []
                    for j in range(0, len(bits), 8):
                        byte_val = 0
                        for k in range(min(8, len(bits) - j)):
                            byte_val = (byte_val << 1) | bits[j + k]
                        
                        # パディング（8ビット未満の場合の左シフト処理）
                        if len(bits) - j < 8:
                            byte_val <<= (8 - (len(bits) - j))
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
                
                burst_count += 1
                    
        print(f"完了: {input_filename} -> {output_filename} ({burst_count} bursts, {frame_count} frames)")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode 3600 bps burst format AMBE audio files to WAV using FEC demodulation")
    parser.add_argument("--input", "-i", required=True, help="Input burst format file (3600 format)")
    parser.add_argument("--output", "-o", required=True, help="Output WAV file")
    args = parser.parse_args()
    
    decode_burst_ambe_via_fec(args.input, args.output)
