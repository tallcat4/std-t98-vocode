import os
import argparse
from pyambelib import fec_demod

def process_single_frame_payload(payload_3600):
    """
    9バイトの3600bpsペイロードを受け取り、fec_demodを経て
    7バイトの2450bpsペイロードを返すヘルパー関数
    """
    # fec_demodを実行してビットストリームを取得 (リスト[int])
    try:
        bits = fec_demod(payload_3600)
    except Exception:
        # エラー時は無音(ゼロ)を返す
        return b'\x00' * 7
    
    # ビットのリストをバイト列に変換（MSB first）
    bytes_from_bits = []
    for i in range(0, len(bits), 8):
        byte_val = 0
        chunk_len = min(8, len(bits) - i)
        for j in range(chunk_len):
            byte_val = (byte_val << 1) | bits[i + j]
        
        # パディング
        if chunk_len < 8:
            byte_val <<= (8 - chunk_len)
        
        bytes_from_bits.append(byte_val)
    
    # 2450モードは49bit -> 7byte
    if len(bytes_from_bits) >= 7:
        return bytes(bytes_from_bits[:7])
    else:
        return b'\x00' * 7

def convert_burst_3600_to_2450(input_filename, output_filename):
    if not os.path.exists(input_filename):
        print(f"File not found: {input_filename}")
        return

    INPUT_BURST_HEADER = b'\xFF'
    INPUT_FRAME_SIZE = 10  # 1 byte Header(0x48) + 9 bytes Data
    FRAMES_PER_BURST = 4
    INPUT_BURST_SIZE = 1 + (INPUT_FRAME_SIZE * FRAMES_PER_BURST) # 41 bytes
    
    OUTPUT_FRAME_HEADER = b'\x31'

    burst_count = 0
    sync_lost_count = 0

    print(f"Converting {input_filename} -> {output_filename} ...")

    with open(input_filename, 'rb') as fin, open(output_filename, 'wb') as fout:
        while True:
            # 1バイト読み込んでヘッダ(0xFF)を探す（同期サーチ）
            header_byte = fin.read(1)
            if not header_byte:
                break # EOF
            
            if header_byte != INPUT_BURST_HEADER:
                # 0xFFでない場合、次のバイトへ（同期外れ）
                sync_lost_count += 1
                continue
            
            # 0xFFが見つかったら、残りの40バイト(バーストの残り)を読み込む
            remaining_burst = fin.read(INPUT_BURST_SIZE - 1)
            if len(remaining_burst) != (INPUT_BURST_SIZE - 1):
                break # ファイル末尾でデータ不足
            
            # チャンクを再構築 (0xFF + 残り)
            chunk = header_byte + remaining_burst
            
            # 出力用バッファ (0xFFから開始)
            output_buffer = bytearray(INPUT_BURST_HEADER)

            # 4フレーム処理
            for i in range(FRAMES_PER_BURST):
                offset = 1 + (i * INPUT_FRAME_SIZE)
                
                # フレームヘッダ(0x48)チェック（参考程度）
                frame_header = chunk[offset]
                # 0x48でない場合も、FECがある程度直してくれることを期待して処理は続ける
                
                payload_3600 = chunk[offset+1 : offset+10]
                payload_2450 = process_single_frame_payload(payload_3600)
                
                output_buffer.extend(OUTPUT_FRAME_HEADER)
                output_buffer.extend(payload_2450)
            
            fout.write(output_buffer)
            burst_count += 1

    print(f"Conversion Done.")
    print(f"  Processed Bursts: {burst_count}")
    print(f"  Skipped Bytes (Sync Search): {sync_lost_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert 3600 -> 2450 (with Sync Search)")
    parser.add_argument("--input", "-i", required=True, help="Input burst file (3600)")
    parser.add_argument("--output", "-o", required=True, help="Output burst file (2450)")
    args = parser.parse_args()
    
    convert_burst_3600_to_2450(args.input, args.output)