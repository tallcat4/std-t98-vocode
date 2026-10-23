# std-t98-vocode

STD-T98のAMBEファイルをWAVへ変換する開発用CLIです。3兄弟のうち音声化と明示的FEC変換を担当します。
音声合成とFECには[ambe2-c](https://github.com/tallcat4/ambe2-c)を使います。pyambelibは不要です。

| ツール | 担当 |
|---|---|
| [std-t98-receiver](https://github.com/tallcat4/std-t98-receiver) | RTL-SDR / IQから72-bit `.burst`を保存 |
| [std-t98-cracker](https://github.com/tallcat4/std-t98-cracker) | 明示した方式で鍵解析、指定鍵で49-bit `.burst`へ変換 |
| std-t98-vocode | ファイルからWAV、またはFECだけの変換 |

受信や鍵探索を自動で起動しません。通常の受け渡しは`.burst`、`.ambe`は既存ツールとの互換用です。
バイト順・長さは[FORMAT.md](FORMAT.md)。

## Windowsで準備

Python 3.11以上、Git、64-bit MinGW Cコンパイラが必要です。
このPCのPython 3.14 / GCC 13.2では次の方法でビルドできます。

```powershell
git clone https://github.com/tallcat4/ambe2-c.git ambe2-c-source
git -C ambe2-c-source checkout bfa9c26b203117d65c68303a87968fd7e89855d9
.\build.ps1
python -m pip install -e .
```

`build.ps1`は`build.py`を呼び、固定リビジョンのソースを変更せず`build/ambe2.dll`へビルドします。
ambe2-c付属の参照ベクトル検証も実行します。コンパイラを指定する場合は`-Compiler PATH`を使います。
Python C APIへのリンクは不要です。既存の`pyambelib-source`や`build/pyambelib`は読みません。

Linux/macOSでは同じソース取得後に`python build.py`を実行します（GCC/Clang、`--compiler PATH`も可）。
出力は`build/libambe2.so`または`build/libambe2.dylib`です。Windows以外はこの移行では実機検証していません。
通常はチェックアウトからの実行またはeditable installを使います。
wheelへネイティブライブラリは同梱しません。別置きする場合は環境変数`STD_T98_AMBE2_LIBRARY`にライブラリの絶対パスを指定してください。
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
72-bitの音声化はambe2-cのFEC付きAPIを直接使い、訂正不可フレームには同APIの音声補間を適用します。
49-bitはThumbDV順のAPIで音声化します。明示的`fec`変換は従来どおり49-bit ThumbDV順で保存し、
訂正不可でもbest-effortのビットを保存します（形式には訂正可否を格納する欄がありません）。品質検証にはcrackerのFEC統計/LLRを利用してください。

## 従来のスクリプト

`decode_2450.py`、`decode_3600.py`、それぞれの`_burst.py`、`fec_demod.py`、`fec_demod_burst.py`は従来の`-i / -o`で使用可能です。
内部の検証と失敗時の終了コードを共通化しました。
`decrypt_2450.py`、`decrypt_decode_2450.py`は明示的`-k 0..32767`付きの互換コマンドとして残しています。
新しい系列の追加はcrackerに集約してください。

```powershell
python -m unittest discover -s tests -v
```

元のvocode基準commit: `4ee64c264b6a1d6ff81a8741c4a139044871c0c2`。
ambe2-cの使用リビジョン: `bfa9c26b203117d65c68303a87968fd7e89855d9`。
MIT/ISC等のライセンス・著作権表示は取得した依存ソース内の`LICENSE`、`decoder/LICENSE`、`decoder/include/mbelib.h`に保持します。
実録音は同梱しません。
