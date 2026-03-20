# Design: Wallet Holdings Tracking Feature

## Project
Polymarket Copytrade Tracker - Add current open positions tracking for top traders.

## Problem Statement
Currently the app only tracks historical performance (ROI, win rate, closed trade P&L) but doesn't show what the trader is currently holding. Copytraders need to see the trader's current open positions to follow along and enter the same positions.

## Requirements

### Functional
- [x] After analyzing a trader's strategy, display all current **unresolved/open** positions
- [x] Show for each position:
  - Market name / title
  - Category (politics, crypto, sports, etc.)
  - Direction (Yes/No)
  - Estimated position size in USD
- [x] Calculate net position when multiple trades on same market
- [x] UI integrated into existing "策略分析" tab below the strategy analysis text
- [x] Data from existing The Graph subgraph API (no new external APIs needed)

### Non-Functional
- [x] Keep the same dark theme consistency
- [x] Scrollable table for many positions
- [x] Don't break existing functionality

## Architecture

### Modified Files
- `gui.py` - main file, add:
  - Add holdings Treeview widget to strategy analysis tab
  - Extend `_calculate_strategy()` to extract and aggregate open positions
  - Add method to populate holdings table
  - Reuse existing data structures

### Data Flow

```
1. User selects trader → clicks "🔍 分析该交易者策略"
2. Query subgraph → gets all trades with market data
3. For each trade:
   - If market.resolved == true → ignore (already closed)
   - If market.resolved == false → add to open positions list
4. Aggregate by market:
   - Group all trades by market.id
   - Calculate net position size (balance after offsetting opposite directions)
   - If net position is zero → skip (fully closed)
5. Display open positions in table:
   - Columns: Market Name | Category | Direction | Position Size USD
```

### Position Aggregation Logic

Polymarket each outcome is a separate token:
- Outcome 0 → "No"
- Outcome 1 → "Yes"

For multiple trades in same market:
```
net_position = sum(amount * direction)
where direction = +1 for Yes, -1 for No
```

If net_position == 0 → position is fully closed → don't display.
If net_position > 0 → holding Yes
If net_position < 0 → holding No

### UI Layout

```
Strategy Analysis Tab:
┌─────────────────────────────────────────────────────────┐
│  Strategy Analysis Textbox (existing)                   │
├─────────────────────────────────────────────────────────┤
│  🔍 Analyze Strategy Button (existing)                  │
├─────────────────────────────────────────────────────────┤
│  📊 Current Open Positions (new)                        │
│  ┌─────────────┬──────────┬──────────┬────────────────┐ │
│  │ Market      │ Category │ Direction│ Position Size  │ │
│  ├─────────────┼──────────┼──────────┼────────────────┤ │
│  │ ...        │ ...      │ Yes/No   │ $XXX.XX       │ │
│  └─────────────┴──────────┴──────────┴────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Styling
- Reuse same Treeview style as main trader table (dark theme compatible)
- Table height: ~150px, scrollable when more than 5 positions

## Success Criteria
- [ ] Displays all open positions correctly
- [ ] Aggregates multiple trades correctly
- [ ] UI fits naturally into existing layout
- [ ] Doesn't break existing functionality
- [ ] Works with the existing API rate limits (doesn't require extra queries)

## Risks & Mitigations
- **Risk**: Too many open positions makes tab too long → **Mitigation**: Fixed height with scrollbar
- **Risk**: Some trades on already resolved markets → **Mitigation**: Check `market.resolved` field from API
- **Risk**: API doesn't return resolved status → **Mitigation**: Already getting this field in current query structure

## Dependencies
- No new dependencies needed, uses existing: customtkinter, tkinter.ttk.Treeview, requests
