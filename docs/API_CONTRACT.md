# Group 30 API contract (proposed by Student C)

Status: proposed 20 Oct 2026. Please reply "agreed" in the group chat or comment on the pull request.

Hi all, our four services call each other, so let's fix the contract now. Student C's proposal:

**1. `POST /features`** (every service)
Request: `{"token": "BTC"}`
Response (HTTP 200):
```json
{"token": "BTC", "as_of": "2026-10-20", "features": {"Return20": 0.0831}}
```
Errors: `{"error": "...", ...}` like the brief's example (`Unsupported cryptocurrency` + `supported_tokens`).
Please keep `features` as a flat object of plain numbers (or `null` when not computable).

**2. Who serves what, and in which unit**

| Owner | Feature names (exact spelling) | Unit |
|---|---|---|
| A | `DailyReturn`, `Return5`, `Return20`, `Momentum` | returns as fractions (0.08 = 8%), Momentum in USD |
| B | `MA5`, `MA20`, `TrendStrength` | MA in USD (price), TrendStrength a fraction |
| C | `Volatility20`, `MaxPrice20`, `MaxDrawdown`, `GapRisk` | fractions, MaxPrice20 in USD |
| D | `SMA20Volume`, `RelativeVolume` | volume units, ratio |

Who needs what from whom (so nobody is blocked): C needs `Return20` (A), `MA5` + `MA20` (B).
A needs `TrendStrength` (B), `Volatility20` (C), `RelativeVolume` (D). B needs `Return20` (A), `Volatility20`, `MaxPrice20`, `GapRisk` (C).
D needs `Return20` (A), `MA5`, `MA20` (B), `Volatility20` (C).

**3. Same day for everyone.** Use **Kraken daily candles** (`/0/public/OHLC?pair=XBTUSD&interval=1440`) and **drop the last, unfinished candle**, so
`as_of` is the last completed UTC day in all four services. If one of us used another source or the unfinished day, our features would
describe different days. Windows are 20 days; Volatility20 uses the sample standard deviation; GapRisk is a 20-day mean.

**4. Calling each other.** Env vars `STUDENT_A_API_URL`, `STUDENT_B_API_URL`, `STUDENT_C_API_URL`, `STUDENT_D_API_URL` (base URL, no trailing slash).
Timeout 10 s, never crash if a peer fails (use NaN: XGBoost and LightGBM handle it). Render's free tier sleeps after about 15 minutes, so
please open every `/health` before demos and before marking.

**5. Deadlines (suggested).** `/features` live on Render by **Thu 22 Oct** (it needs no trained model, so deploy it first), predictions by Sat 24 Oct,
Streamlit pages merged by Mon 26 Oct, final testing and report Tue 27 to Wed 28 Oct, submit Thu 29 Oct before 23:59.

**6. Evidence.** Let's each review at least one teammate's pull request (branch protection requires it anyway) and keep short dated meeting notes in the
experiments repo (`docs/meeting-notes.md`).
