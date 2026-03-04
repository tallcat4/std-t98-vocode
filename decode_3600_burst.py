import wave
import os
import argparse
from pyambelib import AmbeDecoder
from burst_common import (
    BURST_HEADER, FRAMES_PER_BURST, FRAME_SIZE_3600, BURST_SIZE_3600,
    read_burst_payloads, fec_demod_to_2450_payload,
    write_wav_header, samples_to_pcm,
)

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
    if not os.path.exists(input_filename):
        print(f"エラー: {input_filename} が見つかりません。")
        return

    decoder = AmbeDecoder()
    
    print(f"Decoding {input_filename} (Burst 3600 FEC demod -> 2450 decode)...")

    try:
        with open(input_filename, 'rb') as fin, wave.open(output_filename, 'wb') as fout:
            write_wav_header(fout)

            burst_count = 0
            frame_count = 0
            
            while True:
                burst_chunk = fin.read(BURST_SIZE_3600)
                if len(burst_chunk) != BURST_SIZE_3600:
                    break
                
                if burst_chunk[0:1] != BURST_HEADER:
                    print(f"Warning: Burst {burst_count} does not start with 0xFF. Sync might be lost.")
                
                payloads = read_burst_payloads(burst_chunk, FRAME_SIZE_3600)
                
                for payload in payloads:
                    payload_for_2450 = fec_demod_to_2450_payload(payload)
                    samples = decoder.decode_2450(payload_for_2450)
                    
                    if samples:
                        fout.writeframes(samples_to_pcm(samples))
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
