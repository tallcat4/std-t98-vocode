import os
import argparse
from pyambelib import fec_demod
from burst_common import FRAME_SIZE_3600, bits_to_bytes

def convert_3600_to_2450(input_filename, output_filename):
    """
    3600形式のAMBEファイルからFEC情報を除去し、2450形式のAMBEファイルに変換する
    
    Input:  Header(1byte 0x48) + Data(9bytes)
    Output: Header(1byte 0x31) + Data(7bytes)
    """
    if not os.path.exists(input_filename):
        print(f"File not found: {input_filename}")
        return

    with open(input_filename, 'rb') as fin, open(output_filename, 'wb') as fout:
        
        frame_count = 0
        
        while True:
            chunk = fin.read(FRAME_SIZE_3600)
            if len(chunk) != FRAME_SIZE_3600:
                break
            
            # ヘッダチェック (通常 0x48)
            if chunk[0] != 0x48:
                pass

            payload_3600 = chunk[1:]  # 9バイトのペイロード
            
            # fec_demodを実行してビットストリームを取得
            bits = fec_demod(payload_3600)
            
            # ビットのリストをバイト列に変換（MSB first）
            bytes_from_bits = bits_to_bytes(bits)
            
            # 2450モード(音声)は49bit -> 7byteに収まるため、先頭7バイトを抽出
            if len(bytes_from_bits) >= 7:
                payload_2450 = bytes(bytes_from_bits[:7])
                
                # 2450形式のヘッダ(0x31) + ペイロード(7byte) を書き込み
                header = b'\x31'
                fout.write(header + payload_2450)
                frame_count += 1
            else:
                print(f"Warning: Frame {frame_count} produced insufficient bits.")

    print(f"Converted {input_filename} -> {output_filename} ({frame_count} frames)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert 3600 bps AMBE files to 2450 bps using FEC demodulation")
    parser.add_argument("--input", "-i", required=True, help="Input AMBE file (3600 format)")
    parser.add_argument("--output", "-o", required=True, help="Output AMBE file (2450 format)")
    args = parser.parse_args()
    
    convert_3600_to_2450(args.input, args.output)