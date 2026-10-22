# std-t98-vocode

STD-T98のAMBEファイルをWAVへ変換する開発用CLIです。3兄弟のうち音声化と明示的FEC変換を担当します。

| ツール | 担当 |
|---|---|
| [std-t98-receiver](https://github.com/tallcat4/std-t98-receiver) | RTL-SDR / IQから72-bit `.burst`を保存 |
| [std-t98-cracker](https://github.com/tallcat4/std-t98-cracker) | 明示した方式で鍵解析、指定鍵で49-bit `.burst`へ変換 |
| std-t98-vocode | ファイルからWAV、またはFECだけの変換 |

受信や鍵探索を自動で起動しません。通常の受け渡しは`.burst`、`.ambe`は既存ツールとの互換用です。
バイト順・長さは[FORMAT.md](FORMAT.md)。

## Windowsで準備

Python 3.11以上と64-bit MinGW Cコンパイラが必要です。ビルド済みpyambelibがある場合はそのまま使えます。
このPCのPython 3.14 / GCC 13.2では次の方法で音声生成を確認しました。

```powershell
git clone https://github.com/tallcat4/pyambelib.git pyambelib-source
git -C pyambelib-source checkout 7dc77dc2d953869287b3838f993d6dc52701e4aa
.\build.ps1
python -m pip install -e .
```

通常の`pip install ./pyambelib-source`は、この依存の現行MSVC設定では数学定数等のビルドエラーになります。
`build.ps1`は同じソースをMinGWでctypes用DLLとしてビルドし、`build/pyambelib`へ配置します。
Python C APIを使わないためPython ABIへのリンクは不要です。依存ソースは変更しません。
CLIはインストール済みpyambelibを優先し、未インストールならこのローカルビルドを読みます。
この方式はチェックアウトからの実行またはeditable install向けです。通常のwheelには別途pyambelibを用意してください。

Linux等では[pyambelib](https://github.com/tallcat4/pyambelib)を先にインストールしてください。
ファイルの`inspect`と`--help`にはボコーダーは不要です。

## 使い方

```powershell
python -m std_t98_vocode inspect capture.burst
# 平文のreceiver出力は72-bitのまま音声化
python -m std_t98_vocode decode capture.burst -o clear.wav
# crackerが指定鍵で変換した49-bit出力
python -m std_t98_vocode decode descrambled.burst -o descrambled.wav
# FECだけ
python -m std_t98_vocode fec capture.burst -o fec.burst
# .ambeは境界がないので明示する
python -m std_t98_vocode decode legacy.ambe --container ambe -o legacy.wav
```

72/49 bitはフレームマーカーから判定します。ファイル形式の判定だけで、秘話の自動判定や鍵探索ではありません。
秘話がかかったままのデータをdecodeしても正しい音声にはなりません。鍵の解析と解除はcrackerで明示的に行います。

WAVは8 kHz / 16-bit signed little-endian / mono、1フレーム160サンプル。
欠けた時間や無通信区間はファイルに記録されていないので補間しません。
破損した長さ、マーカー、49-bit paddingはエラーです。FFを検索して勝手に同期し直すことはしません。
上書きは拒否します。終了コード0=成功、1=処理エラー（引数エラーはargparseの2）。
pyambelibのFEC APIは訂正不能状態を返しません。品質検証にはcrackerのFEC統計/LLRも利用してください。

## 従来のスクリプト

`decode_2450.py`、`decode_3600.py`、それぞれの`_burst.py`、`fec_demod.py`、`fec_demod_burst.py`は従来の`-i / -o`で使用可能です。
内部の検証と失敗時の終了コードを共通化しました。
`decrypt_2450.py`、`decrypt_decode_2450.py`は明示的`-k 0..32767`付きの互換コマンドとして残しています。
新しい系列の追加はcrackerに集約してください。

```powershell
python -m unittest discover -s tests -v
```

元のvocode基準commit: `4ee64c264b6a1d6ff81a8741c4a139044871c0c2`。
pyambelib/mbelib-neoのライセンスと著作権は取得した依存ソース内に保持します。実録音は同梱しません。
