import os
import argparse
from burst_common import (
    BURST_HEADER, FRAMES_PER_BURST,
    FRAME_SIZE_3600, BURST_SIZE_3600, FRAME_HEADER_2450,
    fec_demod_to_2450_payload,
)

def convert_burst_3600_to_2450(input_filename, output_filename):
    if not os.path.exists(input_filename):
        print(f"File not found: {input_filename}")
        return

    OUTPUT_FRAME_HEADER = bytes([FRAME_HEADER_2450])

    burst_count = 0
    sync_lost_count = 0

    print(f"Converting {input_filename} -> {output_filename} ...")

    with open(input_filename, 'rb') as fin, open(output_filename, 'wb') as fout:
        while True:
            # 1バイト読み込んでヘッダ(0xFF)を探す（同期サーチ）
            header_byte = fin.read(1)
            if not header_byte:
                break # EOF
            
            if header_byte != BURST_HEADER:
                # 0xFFでない場合、次のバイトへ（同期外れ）
                sync_lost_count += 1
                continue
            
            # 0xFFが見つかったら、残りのバイト(バーストの残り)を読み込む
            remaining_burst = fin.read(BURST_SIZE_3600 - 1)
            if len(remaining_burst) != (BURST_SIZE_3600 - 1):
                break # ファイル末尾でデータ不足
            
            # チャンクを再構築 (0xFF + 残り)
            chunk = header_byte + remaining_burst
            
            # 出力用バッファ (0xFFから開始)
            output_buffer = bytearray(BURST_HEADER)

            # 4フレーム処理
            for i in range(FRAMES_PER_BURST):
                offset = 1 + (i * FRAME_SIZE_3600)
                
                payload_3600 = chunk[offset+1 : offset+FRAME_SIZE_3600]
                payload_2450 = fec_demod_to_2450_payload(payload_3600)
                
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