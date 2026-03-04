# ThumbDV bit order → AMBE論理bit order の変換テーブル
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
    内部でThumbDVインターリーブの変換を処理する。
    """
    assert len(payloads) == 4 and all(len(p) == 7 for p in payloads)
    assert len(key_196) == 196

    result = []
    for frame_idx in range(4):
        payload = payloads[frame_idx]
        key_slice = key_196[frame_idx * 49 : (frame_idx + 1) * 49]

        raw_bits = []
        for byte_val in payload:
            for bit_pos in range(7, -1, -1):
                raw_bits.append((byte_val >> bit_pos) & 1)
        raw_bits = raw_bits[:49]

        descrambled_bits = [raw_bits[j] ^ key_slice[_THUMBDV_MAP[j]] for j in range(49)]

        val = 0
        for bit in descrambled_bits:
            val = (val << 1) | bit
        val <<= 7
        result.append(val.to_bytes(7, byteorder='big'))

    return result

def generate_pn_sequence_196(initial_state):
    """
    LFSRを使用して1バースト分(196ビット)のPN系列を生成する(多項式: x^15 + x + 1)
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
