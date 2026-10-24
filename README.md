# std-t98-vocode

STD-T98の`.burst` / `.ambe`をWAVへ変換するCLIです。音声合成には[ambe2-c](https://github.com/tallcat4/ambe2-c)を使います。

## 主な機能

- **WAVへの音声化**：受信した72-bitのAMBEフレームと、FEC除去・秘話解除後の49-bitフレームに対応します。ビット数はファイルのマーカーから判定します。
- **FECだけの変換**：音声化せず、72-bitフレームを誤り訂正して49-bitへ変換できます。
- **ファイルの確認**：`inspect`で形式・フレーム数・音声時間を確認し、長さやマーカーの破損を検出します。
- **旧形式との互換性**：バースト境界のない`.ambe`も読み込めます。従来の`decode_2450.py`などのスクリプトも使用できます。

## セットアップ

WindowsではPython 3.11以上、Git、64-bit MinGW（GCC）が必要です。

```powershell
git clone https://github.com/tallcat4/ambe2-c.git ambe2-c-source
git -C ambe2-c-source checkout 70e32cbfc1cf5a08f3e9a3fbe41f6a9873cc4ca6
.\build.ps1
python -m pip install -e .
```

既存環境を更新する場合は、`ambe2-c-source`で`git fetch`後に上記リビジョンへ切り替え、`build.ps1`を再実行してください。

## 使い方

```powershell
python -m std_t98_vocode inspect clear.burst
python -m std_t98_vocode decode clear.burst -o clear.wav
python -m std_t98_vocode decode legacy.ambe --container ambe -o legacy.wav
# FEC変換だけ行う場合
python -m std_t98_vocode fec capture.burst -o fec.burst
```

WAVは8 kHz・16-bit・モノラルです。秘話付きデータは先に[std-t98-cracker](https://github.com/tallcat4/std-t98-cracker)で解除してください。
受信は[std-t98-receiver](https://github.com/tallcat4/std-t98-receiver)を使います。
[ファイル形式](FORMAT.md)。その他のオプションは各コマンドの`--help`で確認できます。
