# PoH Scripts

PoHに参加するための各種スクリプトです。各スクリプトの詳細はソースコード内のコメントを参照してください。

## チケット残使用回数の確認方法

### 1. castコマンドで確認（推奨）
Foundryがインストールされている場合、以下のコマンドで直接オンチェーン情報を参照できます。

```bash
cast call 0x8Ad615dA799E4c233028b1643030F802AA857f34 \
  "usesRemaining(uint256)(uint8)" <TOKEN_ID> \
  --rpc-url https://mainnet.base.org
```

### 2. player_check.py を使用
より詳細な情報（発行者や所有状態のスキャン）を確認したい場合は、`operator`ディレクトリにあるツールを使用してください。

```bash
python3 ~/poh-contract/operator/player_check.py --token-id <TOKEN_ID>
```
