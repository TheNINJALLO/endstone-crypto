# Crypto Market GUI Flow Diagram

## Main Menu Structure

```
/crypto (no args)
    │
    ├─► Main Menu
        │
        ├─► 🟢 Buy Crypto
        │   │
        │   ├─► Coin Selection Menu
        │   │   │
        │   │   ├─► NINJ ($X.XX)
        │   │   ├─► DIAM ($X.XX)
        │   │   ├─► EMER ($X.XX)
        │   │   ├─► ... (30+ coins)
        │   │   └─► « Back
        │   │
        │   └─► Buy Form (for selected coin)
        │       │
        │       ├─► Shows: Chart, Price, Fee, Your Money
        │       ├─► Input: Quantity
        │       ├─► Button: Buy Now
        │       └─► On Close: Back to Coin Selection
        │
        ├─► 🔴 Sell Crypto
        │   │
        │   ├─► Owned Coins Menu
        │   │   │
        │   │   ├─► NINJ (X.XXXX owned)
        │   │   ├─► DIAM (X.XXXX owned)
        │   │   ├─► ... (only owned coins)
        │   │   └─► « Back
        │   │
        │   └─► Sell Form (for selected coin)
        │       │
        │       ├─► Shows: Chart, Price, Fee, Your Holdings
        │       ├─► Input: Quantity
        │       ├─► Button: Sell Now
        │       └─► On Close: Back to Owned Coins
        │
        ├─► 📘 My Portfolio
        │   │
        │   └─► Portfolio View
        │       │
        │       ├─► Shows: Money, Credits, Total Value
        │       ├─► Lists: All Holdings with Values
        │       └─► Button: « Back
        │
        ├─► 💹 Market Prices
        │   │
        │   ├─► Prices List
        │   │   │
        │   │   ├─► Button: NINJ Chart
        │   │   ├─► Button: DIAM Chart
        │   │   ├─► ... (all coins)
        │   │   └─► Button: « Back
        │   │
        │   └─► Chart View (for selected coin)
        │       │
        │       ├─► Shows: Name, Chart, Price
        │       ├─► Button: Buy
        │       ├─► Button: Sell
        │       └─► Button: « Back
        │
        ├─► 🤝 P2P Trading
        │   │
        │   ├─► P2P Menu
        │   │   │
        │   │   ├─► Create Offer
        │   │   ├─► View All Offers
        │   │   ├─► My Offers
        │   │   └─► « Back
        │   │
        │   ├─► Create Offer Form
        │   │   │
        │   │   ├─► Dropdown: Select Coin
        │   │   ├─► Input: Quantity
        │   │   ├─► Input: Price Per Coin
        │   │   ├─► Input: Target Player (optional)
        │   │   ├─► Button: Create Offer
        │   │   └─► On Close: Back to P2P Menu
        │   │
        │   ├─► View All Offers
        │   │   │
        │   │   └─► Shows offers in chat, returns to P2P Menu
        │   │
        │   └─► My Offers
        │       │
        │       └─► Shows your offers in chat, returns to P2P Menu
        │
        ├─► 📥 Deposit Money
        │   │
        │   └─► Deposit Form
        │       │
        │       ├─► Shows: Internal Credits Balance
        │       ├─► Input: Amount to Deposit
        │       ├─► Button: Deposit
        │       ├─► Action: Credits → Money Scoreboard
        │       └─► On Close: Back to Main Menu
        │
        └─► 📤 Withdraw Money
            │
            └─► Withdraw Form
                │
                ├─► Shows: Money Scoreboard Balance
                ├─► Input: Amount to Withdraw
                ├─► Button: Withdraw
                ├─► Action: Money Scoreboard → Credits
                └─► On Close: Back to Main Menu
```

## Transaction Flow

### Buying Crypto
```
1. Player opens /crypto
2. Clicks "Buy Crypto"
3. Selects a coin (e.g., NINJ)
4. Views chart and current price
5. Enters quantity (e.g., 10.5)
6. System calculates: Cost = Price × Qty × (1 + Fee)
7. Validates: Player has enough Money
8. Deducts Money from scoreboard
9. Adds crypto to holdings
10. Saves holdings
11. Confirms transaction
```

### Selling Crypto
```
1. Player opens /crypto
2. Clicks "Sell Crypto"
3. Selects owned coin (e.g., DIAM)
4. Views chart and current price
5. Enters quantity (e.g., 5.25)
6. System calculates: Proceeds = Price × Qty × (1 - Fee)
7. Validates: Player has enough holdings
8. Deducts crypto from holdings
9. Adds Money to scoreboard
10. Saves holdings
11. Confirms transaction
```

### P2P Trading
```
1. Player opens /crypto
2. Clicks "P2P Trading"
3. Clicks "Create Offer"
4. Selects coin from dropdown
5. Enters quantity, price, target player
6. System validates holdings
7. Creates offer in system
8. Other players can accept via:
   - GUI: "View All Offers" → chat list → /crypto accept <id>
   - Command: /crypto accept <id>
```

### Deposit/Withdraw
```
Deposit (Credits → Money):
1. Player opens /crypto
2. Clicks "Deposit Money"
3. Enters amount
4. System validates credits balance
5. Deducts from internal credits
6. Adds to Money scoreboard
7. Confirms transfer

Withdraw (Money → Credits):
1. Player opens /crypto
2. Clicks "Withdraw Money"
3. Enters amount
4. System validates Money balance
5. Deducts from Money scoreboard
6. Adds to internal credits
7. Confirms transfer
```

## Form Types Used

### ActionForm (Menus)
- Main Menu
- Buy Coin Selection
- Sell Coin Selection
- Portfolio View
- Market Prices List
- Chart View
- P2P Menu

### ModalForm (Input Forms)
- Buy Form (with quantity input)
- Sell Form (with quantity input)
- Create P2P Offer (with multiple inputs)
- Deposit Form (with amount input)
- Withdraw Form (with amount input)

## Navigation Patterns

### Back Button Behavior
- All menus have "« Back" button
- Returns to previous menu in hierarchy
- Forms use `on_close` callback for back navigation

### Form Submission
- ModalForms use `on_submit` callback
- Validates input before processing
- Shows error messages for invalid input
- Returns to appropriate menu after success

### Error Handling
- Invalid input → Error message + stay on form
- Insufficient funds → Error message + return to menu
- Insufficient holdings → Error message + return to menu
- Network/scoreboard errors → Logged + error message

## Color Coding

### Menu Items
- 🟢 Green (§2) - Buy/Positive actions
- 🔴 Red (§c) - Sell/Negative actions
- 📘 Blue (§b) - Information/View
- 💹 Yellow (§e) - Market/Prices
- 🤝 Gold (§6) - Trading
- 📥 Aqua (§3) - Deposit
- 📤 Purple (§d) - Withdraw
- ⬅️ Gray (§8) - Back/Cancel

### Text Colors
- §a - Green (positive values, success)
- §c - Red (errors, warnings)
- §e - Yellow (money, prices)
- §b - Blue (info, labels)
- §7 - Gray (descriptions)
- §l - Bold (titles, headers)

## User Experience Features

### Real-time Information
- Current Money balance shown in all relevant forms
- Current holdings shown when selling
- Live price updates (from price tick system)
- ASCII charts for visual price trends

### Input Validation
- Numeric validation for all quantity/amount inputs
- Balance checks before transactions
- Holdings checks before sales
- Positive number enforcement

### Feedback
- Success messages after transactions
- Error messages for failures
- Confirmation of amounts and fees
- Clear display of transaction results

### Accessibility
- Both GUI and commands available
- GUI for ease of use
- Commands for power users and automation
- All features accessible both ways

