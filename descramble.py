# ThumbDV bit order → AMBE論理bit order の変換テーブル
# libambe_wrapper.c の process_ambe2450 で使用されている thumbdv_map と同一
# raw_bits[i] は ambe_d[_THUMBDV_MAP[i]] に対応する
_THUMBDV_MAP = [
     0, 18, 36,  1, 19, 37,  2, 20, 38,
     3, 21, 39,  4, 22, 40,  5, 23, 41,
     6, 24, 42,  7, 25, 43,  8, 26, 44,
     9, 27, 45, 10, 28, 46, 11, 29, 47,
    12, 30, 48, 13, 31, 14, 32, 15, 33,
    16, 34, 17, 35
]

def descramble_burst(payloads, key_196):
    """
    1バースト分(4フレーム)のスクランブル解除を行う。
    内部で ThumbDV インターリーブの変換を処理するため、
    呼び出し側はインターリーブを意識する必要がない。

    Args:
        payloads: 4フレーム分のペイロード (list[bytes])。各要素は7バイト。
        key_196:  196ビットの鍵 (list[int], 各要素0 or 1)。
                  AMBE論理ビット順。先頭49ビットがフレーム0、次の49ビットがフレーム1、...

    Returns:
        list[bytes]: スクランブル解除済みの4フレーム分のペイロード (各7バイト)
    """
    assert len(payloads) == 4 and all(len(p) == 7 for p in payloads)
    assert len(key_196) == 196

    result = []
    for frame_idx in range(4):
        payload = payloads[frame_idx]
        key_slice = key_196[frame_idx * 49 : (frame_idx + 1) * 49]

        # 7バイトを49ビットに展開 (MSB first)
        raw_bits = []
        for byte_val in payload:
            for bit_pos in range(7, -1, -1):
                raw_bits.append((byte_val >> bit_pos) & 1)
        raw_bits = raw_bits[:49]

        # _THUMBDV_MAP に従い、鍵を並び替えてから XOR
        descrambled_bits = [raw_bits[j] ^ key_slice[_THUMBDV_MAP[j]] for j in range(49)]

        # 49ビットを7バイトに再パック (MSB first, 末尾7ビットは0パディング)
        val = 0
        for bit in descrambled_bits:
            val = (val << 1) | bit
        val <<= 7
        result.append(val.to_bytes(7, byteorder='big'))

    return result

def generate_pn_sequence_196(initial_state):
    """
    LFSRを使用して1バースト分(196ビット)のPN系列を生成する
    多項式: x^15 + x + 1

    Args:
        initial_state: LFSRの初期値 (0~32767)

    Returns:
        list[int]: 196ビットのPN系列 (各要素0 or 1)
    """
    state = initial_state
    pn_bits = []

    for _ in range(196):
        output = state & 1
        pn_bits.append(output)

        s0 = state & 1
        s1 = (state >> 1) & 1
        feedback = s0 ^ s1

        state = state >> 1
        if feedback:
            state |= (1 << 14)

    return pn_bits
