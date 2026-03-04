import wave
import os
import argparse
from pyambelib import AmbeDecoder
from burst_common import (
    BURST_HEADER, FRAMES_PER_BURST, FRAME_SIZE_2450, BURST_SIZE_2450,
    read_burst_payloads, write_wav_header, samples_to_pcm,
)

def decode_burst_ambe_2450(input_filename, output_filename):
    """
    バースト形式の2450 AMBEファイルをWAVにデコードする
    """
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return

    decoder = AmbeDecoder()
    
    print(f"Decoding {input_filename} (Burst 2450 decode)...")

    try:
        with open(input_filename, 'rb') as fin, wave.open(output_filename, 'wb') as fout:
            write_wav_header(fout)

            burst_count = 0
            frame_count = 0
            
            while True:
                burst_chunk = fin.read(BURST_SIZE_2450)
                if len(burst_chunk) != BURST_SIZE_2450:
                    break
                
                if burst_chunk[0:1] != BURST_HEADER:
                    print(f"Warning: Burst {burst_count} does not start with 0xFF. Sync might be lost.")
                
                payloads = read_burst_payloads(burst_chunk, FRAME_SIZE_2450)
                
                for payload in payloads:
                    samples = decoder.decode_2450(payload)
                    
                    if samples:
                        fout.writeframes(samples_to_pcm(samples))
                        frame_count += 1
                
                burst_count += 1
                    
        print(f"Done: {input_filename} -> {output_filename} ({burst_count} bursts, {frame_count} frames)")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode 2450 bps burst format AMBE audio files to WAV")
    parser.add_argument("--input", "-i", required=True, help="Input burst format file (2450 format)")
    parser.add_argument("--output", "-o", required=True, help="Output WAV file")
    args = parser.parse_args()
    
    decode_burst_ambe_2450(args.input, args.output)
