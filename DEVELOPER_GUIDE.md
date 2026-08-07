# Crypto Market Plugin - Developer Guide

## Architecture Overview

### Core Components

1. **CryptoMarket Plugin** (`crypto_market.py`)
   - Main plugin class extending `Plugin`
   - Handles commands, events, and GUI
   - Manages market state and player holdings

2. **Market State** (`self.state`)
   - `prices`: Dict[symbol, float] - Current prices for all coins
   - `history`: Dict[symbol, Deque[float]] - Price history for charts
   - `momentum`: Dict[symbol, float] - Price momentum for volatility

3. **Holdings System** (`self._holdings`)
   - Dict[uuid_hex, Dict[symbol, float]]
   - Stores player crypto holdings
   - Special key "_credits" for internal currency

4. **Scoreboard Integration**
   - "Money" objective on Minecraft scoreboard
   - Stores player Money balance
   - Auto-created if doesn't exist

## Key Methods

### GUI Methods

```python
def _show_main_menu(self, p: Player)
    # Opens main menu with 7 options
    # Called when player types /crypto with no args

def _show_buy_menu(self, p: Player)
    # Lists all coins for purchase
    # Shows current prices

def _show_buy_form(self, p: Player, symbol: str)
    # ModalForm for buying specific coin
    # Validates funds and processes transaction

def _show_sell_menu(self, p: Player)
    # Lists only coins player owns
    # Shows quantities and values

def _show_sell_form(self, p: Player, symbol: str)
    # ModalForm for selling specific coin
    # Validates holdings and processes transaction

def _show_portfolio(self, p: Player)
    # Displays player's complete portfolio
    # Shows Money, Credits, and total value

def _show_market_prices(self, p: Player)
    # Lists all coins with prices
    # Buttons to view individual charts

def _show_chart(self, p: Player, symbol: str)
    # Shows ASCII chart for coin
    # Quick buy/sell buttons

def _show_p2p_menu(self, p: Player)
    # P2P trading interface
    # Create, view, and manage offers

def _show_deposit_form(self, p: Player)
    # Convert internal credits to Money

def _show_withdraw_form(self, p: Player)
    # Convert Money to internal credits
```

### Scoreboard Methods

```python
def _get_money(self, p: Player) -> int
    # Get player's Money from scoreboard
    # Returns 0 if objective doesn't exist
    # Auto-creates objective if needed

def _set_money(self, p: Player, amount: int)
    # Set player's Money on scoreboard
    # Ensures non-negative value

def _add_money(self, p: Player, delta: int)
    # Add/subtract Money from player
    # Wrapper around _get_money + _set_money
```

### Holdings Methods

```python
def _get_holdings(self, p: Player, symbol: str) -> float
    # Get quantity of specific coin player owns

def _add_holdings(self, p: Player, symbol: str, delta: float)
    # Add/subtract coin quantity

def _get_root(self, p: Player) -> Dict
    # Get player's holdings dict

def _save_holdings_for(self, p: Player)
    # Save holdings to disk for specific player

def _save_holdings()
    # Save all holdings to disk
```

### Utility Methods

```python
def _coin_spec(self, symbol: str) -> CoinSpec
    # Get coin configuration

def _coin_symbols() -> List[str]
    # Get all coin symbols

def _mini_chart(self, symbol: str, tall: bool = False) -> str
    # Generate ASCII chart for coin
    # tall=True for detailed view
```

## Form Patterns

### ActionForm Pattern
```python
form = ActionForm(
    title="§l§6Menu Title",
    content="§7Description text"
)

form.add_button(
    "§l§2Button Label",
    icon="textures/ui/icon_name",
    on_click=lambda pl: self._next_method(pl)
)

form.add_button("§l§8« Back", on_click=lambda pl: self._show_main_menu(pl))

p.send_form(form)
```

### ModalForm Pattern
```python
form = ModalForm(
    title="§l§6Form Title",
    submit_button="§l§aSubmit"
)

form.add_control(Label("§7Description"))
form.add_control(TextInput(label="§eLabel", placeholder="hint"))
form.add_control(Dropdown(label="§eSelect", options=["Option1", "Option2"]))

def on_submit(pl: Player, data: str):
    import json
    vals = json.loads(data)
    # vals[0] = Label (not in data)
    # vals[1] = TextInput value
    # vals[2] = Dropdown index
    # Process and validate
    # Show error or success message

form.on_submit = on_submit
form.on_close = lambda pl: self._show_previous_menu(pl)

p.send_form(form)
```

## Transaction Processing

### Buy Transaction
```python
# 1. Get current price
price = self.state["prices"][symbol]

# 2. Calculate total with fee
fee = spec.fee_bps / 10000.0
total = math.ceil(price * qty * (1.0 + fee))

# 3. Validate funds
current_money = self._get_money(player)
if current_money < total:
    player.send_message("§c[Crypto] Insufficient funds")
    return

# 4. Execute transaction
self._set_money(player, current_money - total)
self._add_holdings(player, symbol, +qty)
self._save_holdings_for(player)

# 5. Confirm
player.send_message(f"§a[Crypto] Bought {qty:.4f} {symbol}")
```

### Sell Transaction
```python
# 1. Get current price
price = self.state["prices"][symbol]

# 2. Calculate proceeds after fee
fee = spec.fee_bps / 10000.0
proceeds = math.floor(price * qty * (1.0 - fee))

# 3. Validate holdings
current_holdings = self._get_holdings(player, symbol)
if current_holdings < qty:
    player.send_message("§c[Crypto] Insufficient holdings")
    return

# 4. Execute transaction
self._set_money(player, current_money + proceeds)
self._add_holdings(player, symbol, -qty)
self._save_holdings_for(player)

# 5. Confirm
player.send_message(f"§a[Crypto] Sold {qty:.4f} {symbol}")
```

## Error Handling

### Input Validation
```python
try:
    qty = float(qty_str)
    if qty <= 0:
        player.send_message("§c[Crypto] Quantity must be > 0")
        return
except ValueError:
    player.send_message("§c[Crypto] Invalid quantity")
    return
```

### Scoreboard Error Handling
```python
try:
    scoreboard = self.server.scoreboard
    objective = scoreboard.get_objective("Money")
    if objective is None:
        objective = scoreboard.add_objective("Money", "dummy", "§6Money")
    score = objective.get_score(player)
    return score.value if score else 0
except Exception as e:
    self.logger.warning(f"Failed to get Money: {e}")
    return 0
```

## Configuration

### Coin Configuration (config.toml)
```toml
[[coins]]
symbol = "NINJ"
name = "Ninja Coin"
start_price = 100.0
min_price = 10.0
max_price = 1000.0
volatility = 0.05
mining_weight = 1.0
momentum = 0.1
fee_bps = 50  # 0.5% fee
```

### Plugin Configuration
- `holdings.json` - Player holdings storage
- `config.toml` - Coin specifications
- Scoreboard "Money" - Player Money balance

## Event Handlers

### Block Break Event
```python
@event_handler
def on_block_break(self, event: BlockBreakEvent):
    # Award mining drops based on ore type
    # Uses mining_weight from coin config
```

### Player Join Event
```python
@event_handler
def on_player_join(self, event: PlayerJoinEvent):
    # Initialize player holdings if needed
```

## Command Handler

### Main Command Entry Point
```python
def on_command(self, sender: CommandSender, command: Command, args: List[str]) -> bool:
    if command.name != "crypto":
        return False
    
    if not isinstance(sender, Player):
        sender.send_message("[Crypto] Use this in-game.")
        return True
    
    # No args -> open GUI
    if not parts:
        self._show_main_menu(sender)
        return True
    
    # Subcommands for backward compatibility
    # ...
```

## Testing Checklist

- [ ] Buy crypto with Money
- [ ] Sell crypto for Money
- [ ] Deposit credits to Money
- [ ] Withdraw Money to credits
- [ ] Create P2P offer via GUI
- [ ] View portfolio
- [ ] View market prices
- [ ] View charts
- [ ] Error handling (insufficient funds)
- [ ] Error handling (invalid input)
- [ ] Scoreboard Money updates correctly
- [ ] Holdings persist after reload
- [ ] Multiple players simultaneously
- [ ] All backward-compatible commands work

## Performance Considerations

1. **Holdings Caching**
   - Holdings loaded into memory on startup
   - Saved to disk after each transaction
   - Consider caching for large player bases

2. **Price Updates**
   - Price tick runs every 20 ticks (1 second)
   - Updates all coin prices
   - Regenerates charts

3. **Scoreboard Access**
   - Scoreboard access is relatively fast
   - Objective auto-created on first access
   - Consider caching objective reference

## Future Enhancements

1. **Database Backend**
   - Replace JSON with database
   - Better performance for large servers

2. **Advanced Trading**
   - Limit orders
   - Stop losses
   - Portfolio tracking

3. **Leaderboards**
   - Richest players
   - Most traded coins
   - Trading volume

4. **Analytics**
   - Transaction history
   - Price statistics
   - Player statistics

5. **Customization**
   - Per-player trading fees
   - Custom coin lists
   - Price manipulation controls

