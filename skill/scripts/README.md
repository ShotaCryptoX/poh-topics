# PoH Scripts

Scripts for participating in PoH. See the source code comments for detailed usage of each script.

## How to Check Remaining Ticket Uses

### 1. Using the `cast` command (Recommended)
If you have Foundry installed, you can query on-chain data directly.

```bash
cast call 0x8Ad615dA799E4c233028b1643030F802AA857f34 \
  "usesRemaining(uint256)(uint8)" <TOKEN_ID> \
  --rpc-url https://mainnet.base.org
```

### 2. Using the script
For a simpler check, use `submit_answer.py` with the `--dry-run` flag — it verifies ticket ownership and remaining uses before submitting.

```bash
python submit_answer.py --round <ROUND_ID> --ticket <TOKEN_ID> --answer "test" --dry-run
```
