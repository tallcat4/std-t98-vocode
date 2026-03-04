"""
AMBE バースト処理の共通モジュール

バースト形式の定数、ペイロード抽出、WAV出力、
ビット列変換などの共通機能を提供する。
"""
import struct
from pyambelib import fec_demod

# ── バースト共通定数 ──
BURST_HEADER = b'\xFF'
FRAMES_PER_BURST = 4

# ── 2450形式 ──
FRAME_HEADER_2450 = 0x31
FRAME_SIZE_2450 = 8       # 1 byte Header + 7 bytes Data
PAYLOAD_SIZE_2450 = 7
BURST_SIZE_2450 = 1 + (FRAME_SIZE_2450 * FRAMES_PER_BURST)  # 33 bytes

# ── 3600形式 ──
FRAME_HEADER_3600 = 0x48
FRAME_SIZE_3600 = 10      # 1 byte Header + 9 bytes Data
PAYLOAD_SIZE_3600 = 9
BURST_SIZE_3600 = 1 + (FRAME_SIZE_3600 * FRAMES_PER_BURST)  # 41 bytes


def read_burst_payloads(burst_chunk, frame_size):
    """
    バーストチャンクから4フレーム分のペイロードを抽出する。

    Args:
        burst_chunk: バースト全体のバイト列 (先頭の0xFFを含む)
        frame_size:  1フレームのサイズ (ヘッダ+データ)

    Returns:
        list[bytes]: 4フレーム分のペイロード
    """
    payloads = []
    for i in range(FRAMES_PER_BURST):
        offset = 1 + (i * frame_size)
        payloads.append(burst_chunk[offset + 1 : offset + frame_size])
    return payloads


def bits_to_bytes(bits):
    """
    ビット列(list[int])をバイト列に変換する（MSB first）。
    8ビット未満の端数は左詰めでパディング。

    Args:
        bits: ビットのリスト (各要素 0 or 1)

    Returns:
        list[int]: バイト値のリスト
    """
    result = []
    for i in range(0, len(bits), 8):
        byte_val = 0
        chunk_len = min(8, len(bits) - i)
        for j in range(chunk_len):
            byte_val = (byte_val << 1) | bits[i + j]
        if chunk_len < 8:
            byte_val <<= (8 - chunk_len)
        result.append(byte_val)
    return result


def fec_demod_to_2450_payload(payload_3600):
    """
    9バイトの3600bpsペイロードをFEC復調し、
    7バイトの2450bpsペイロードに変換する。

    Args:
        payload_3600: 9バイトの3600bpsペイロード

    Returns:
        bytes: 7バイトの2450bpsペイロード
    """
    try:
        bits = fec_demod(payload_3600)
    except Exception:
        return b'\x00' * 7

    bytes_from_bits = bits_to_bytes(bits)

    if len(bytes_from_bits) >= 7:
        return bytes(bytes_from_bits[:7])
    else:
        return b'\x00' * 7


def write_wav_header(wav_file):
    """
    WAVファイルに 8kHz / 16bit / Mono の設定を書き込む。

    Args:
        wav_file: wave.open() で開いたファイルオブジェクト
    """
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(8000)


def samples_to_pcm(samples):
    """
    intサンプルリストをPCMバイト列 (Little Endian, 16bit signed) に変換する。

    Args:
        samples: 音声サンプルのリスト (int)

    Returns:
        bytes: PCMバイト列
    """
    return struct.pack(f'<{len(samples)}h', *samples)
