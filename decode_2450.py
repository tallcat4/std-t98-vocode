import wave
import os
import argparse
from pyambelib import AmbeDecoder
from burst_common import FRAME_SIZE_2450, write_wav_header, samples_to_pcm

def decode_output_ambe_2450(input_filename, output_filename):
    """
    2450bps形式のAMBEファイルをWAVにデコードする
    """
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return

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
                
                if chunk[0] != 0x31:
                    pass

                payload = chunk[1:]
                
                samples = decoder.decode_2450(payload)
                
                if samples:
                    fout.writeframes(samples_to_pcm(samples))
                    frame_count += 1
                    
        print(f"Done: {input_filename} -> {output_filename} ({frame_count} frames)")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode 2450 bps AMBE audio files to WAV")
    parser.add_argument("--input", "-i", required=True, help="Input AMBE file (2450 format)")
    parser.add_argument("--output", "-o", required=True, help="Output WAV file")
    args = parser.parse_args()
    
    decode_output_ambe_2450(args.input, args.output)