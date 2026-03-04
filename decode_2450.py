import wave
import os
import argparse
from pyambelib import AmbeDecoder
from burst_common import FRAME_SIZE_2450, write_wav_header, samples_to_pcm

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
            write_wav_header(fout)

            frame_count = 0
            
            while True:
                chunk = fin.read(FRAME_SIZE_2450)
                if len(chunk) != FRAME_SIZE_2450:
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
                    fout.writeframes(samples_to_pcm(samples))
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