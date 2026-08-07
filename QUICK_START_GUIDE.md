# Crypto Market Plugin - Quick Start Guide

## Installation

1. Download `endstone_crypto-3.0.0-py3-none-any.whl`
2. Place in your Endstone plugins directory
3. Restart server
4. The "Money" scoreboard objective will be created automatically

## Getting Started

### Opening the GUI
Simply type:
```
/crypto
```

This opens the main menu with all available options.

## Main Features

### 1. Buying Crypto

**Steps:**
1. Type `/crypto`
2. Click "🟢 Buy Crypto"
3. Select a coin from the list
4. Enter the quantity you want to buy
5. Click "Buy Now"

**What happens:**
- Money is deducted from your scoreboard
- Crypto is added to your holdings
- Transaction fee is applied (0.5% by default)

**Example:**
- Price: $100 per NINJ
- Quantity: 10
- Fee: 0.5%
- Total Cost: $1,005

### 2. Selling Crypto

**Steps:**
1. Type `/crypto`
2. Click "🔴 Sell Crypto"
3. Select a coin you own
4. Enter the quantity you want to sell
5. Click "Sell Now"

**What happens:**
- Crypto is removed from your holdings
- Money is added to your scoreboard
- Transaction fee is deducted (0.5% by default)

**Example:**
- Price: $100 per DIAM
- Quantity: 5
- Fee: 0.5%
- Total Proceeds: $497.50

### 3. Viewing Your Portfolio

**Steps:**
1. Type `/crypto`
2. Click "📘 My Portfolio"

**You'll see:**
- Your current Money balance
- Your internal credits balance
- Total value of all your crypto
- Detailed list of each coin you own

### 4. Checking Market Prices

**Steps:**
1. Type `/crypto`
2. Click "💹 Market Prices"
3. Click any coin to see its chart

**You'll see:**
- Current price
- ASCII price chart showing trends
- Quick Buy/Sell buttons

### 5. P2P Trading (Player-to-Player)

**Creating an Offer:**
1. Type `/crypto`
2. Click "🤝 P2P Trading"
3. Click "Create Offer"
4. Select a coin you own
5. Enter quantity and price per coin
6. Optionally enter target player name
7. Click "Create Offer"

**Accepting an Offer:**
1. Type `/crypto`
2. Click "🤝 P2P Trading"
3. Click "View All Offers"
4. Find the offer you want
5. Use `/crypto accept <offer_id>`

**Managing Your Offers:**
1. Type `/crypto`
2. Click "🤝 P2P Trading"
3. Click "My Offers"
4. Use `/crypto cancel <offer_id>` to cancel

### 6. Money Management

**Deposit (Credits → Money):**
1. Type `/crypto`
2. Click "📥 Deposit Money"
3. Enter amount to convert
4. Click "Deposit"

**Withdraw (Money → Credits):**
1. Type `/crypto`
2. Click "📤 Withdraw Money"
3. Enter amount to convert
4. Click "Withdraw"

## Earning Crypto

### Mining
Break ores to earn crypto! Different ores give different coins:
- Diamond ore → DIAM
- Emerald ore → EMER
- Gold ore → GOLD
- Iron ore → IRON
- And more!

The amount you earn depends on the ore type and coin configuration.

## Understanding Money vs Credits

### Money (Scoreboard)
- Displayed in your scoreboard
- Used for buying/selling crypto
- Can be seen by other players
- Persistent across sessions

### Internal Credits
- Legacy system for backward compatibility
- Can be converted to/from Money
- Used in some commands
- Stored in plugin data

**Tip:** Use Money for all transactions. Credits are mainly for compatibility.

## Tips & Tricks

### 1. Watch the Charts
- Charts show price trends
- Use them to decide when to buy/sell
- Prices update every second

### 2. Diversify Your Portfolio
- Don't put all money in one coin
- Different coins have different volatility
- Spread risk across multiple coins

### 3. Use P2P Trading
- Negotiate prices with other players
- Can get better deals than bank prices
- Build trading relationships

### 4. Monitor Your Balance
- Check portfolio regularly
- Track your total value
- Set personal profit targets

### 5. Transaction Fees
- All trades have a 0.5% fee
- Buying: Fee added to cost
- Selling: Fee deducted from proceeds
- Plan accordingly

## Command Reference

### GUI Commands
```
/crypto                    # Open main menu (recommended!)
/crypto help              # Show help text
```

### Information Commands
```
/crypto symbols           # List all coin symbols
/crypto coins             # List coins with prices
/crypto price <symbol>    # Show price of specific coin
/crypto chart <symbol>    # Show ASCII chart
/crypto holdings          # Show your holdings
```

### Trading Commands
```
/crypto market buy <symbol> <qty>      # Buy from bank
/crypto market sell <symbol> <qty>     # Sell to bank
/crypto send <player> <symbol> <qty>   # Send coin to player
```

**Note:** If a player name has spaces, wrap it in quotes: `/crypto send "Player Name" NINJ 5`

### P2P Trading Commands
```
/crypto offer <player> <symbol> <qty> <price>  # Create offer
/crypto offers [mine|all]                      # List offers
/crypto accept <id>                            # Accept offer
/crypto cancel <id>                            # Cancel offer
```

**Note:** If a player name has spaces, wrap it in quotes: `/crypto offer "Player Name" NINJ 5 100`

### Admin Commands
```
/crypto admin help        # Show admin help
/crypto admin reset       # Reset market
/crypto admin set <symbol> <price>  # Set price
```

## Troubleshooting

### "Insufficient funds" error
- You don't have enough Money
- Check your balance in portfolio
- Sell some crypto or deposit credits

### "Insufficient holdings" error
- You don't own that coin
- Check portfolio to see what you own
- Mine ores or buy the coin first

### "Invalid input" error
- Check your quantity/amount format
- Use decimal numbers (e.g., 10.5)
- Ensure positive values only

### Money not updating
- Scoreboard might not be initialized
- Try restarting server
- Check server logs for errors

### Can't see other players' offers
- They might not have created any
- Check "View All Offers" for public offers
- Ask them to create an offer

## FAQ

**Q: How do I get started with no money?**
A: Mine ores! Breaking ores gives you free crypto that you can sell for Money.

**Q: Can I lose money?**
A: Yes, if you buy high and sell low. Prices fluctuate based on market conditions.

**Q: Are prices the same for everyone?**
A: Yes, all players see the same prices at the same time.

**Q: Can I trade with offline players?**
A: No, P2P trading requires both players to be online.

**Q: What happens if I disconnect?**
A: Your holdings and Money are saved. You'll have them when you rejoin.

**Q: Can admins see my Money?**
A: Yes, Money is on the scoreboard which is visible to admins.

**Q: Is there a maximum amount of Money I can have?**
A: No, but very large numbers might cause display issues.

**Q: Can I reset my holdings?**
A: Only admins can reset the market. Contact your server admin.

## Getting Help

- Ask server admins for help
- Check `/crypto help` for command list
- Review this guide for common issues
- Check server logs for error messages

## Have Fun!

The Crypto Market is designed for fun and economy simulation. Enjoy trading, mining, and building your wealth!

