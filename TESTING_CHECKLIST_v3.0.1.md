# Testing Checklist - Version 3.0.1

## Pre-Installation Testing

### ✅ Code Verification
- [x] No syntax errors (`python -m py_compile src/endstone_crypto/crypto_market.py`)
- [x] All unit tests pass (`python test_parse_args.py`)
- [x] Build successful (`python -m build`)
- [x] Wheel file created (`dist/endstone_crypto-3.0.1-py3-none-any.whl`)

### ✅ Documentation Verification
- [x] MEMBER_GUIDE.md updated with quoted player name syntax
- [x] MEMBER_GUIDE_DISCORD.md updated with quoted player name syntax
- [x] QUICK_START_GUIDE.md updated with quoted player name syntax
- [x] CHANGELOG_v3.0.1.md created
- [x] INSTALL_v3.0.1.md created
- [x] SCOREBOARD_COMPATIBILITY_VERIFICATION.md created

## Post-Installation Testing

### Installation
- [ ] Install plugin: `pip install dist/endstone_crypto-3.0.1-py3-none-any.whl --force-reinstall`
- [ ] Restart server
- [ ] Verify plugin loads: Check logs for "Loading plugin: cryptomarket v3.0.1"
- [ ] Verify no errors in server logs

### Basic Functionality (Backward Compatibility)

#### Test 1: Player Without Spaces - Send Command
```bash
/crypto send PlayerName NINJ 5
```
- [ ] Command executes successfully
- [ ] No error messages
- [ ] Crypto transferred correctly
- [ ] Both players receive confirmation messages

#### Test 2: Player Without Spaces - Offer Command
```bash
/crypto offer PlayerName NINJ 5 100
```
- [ ] Command executes successfully
- [ ] Offer created
- [ ] Target player can see and accept offer
- [ ] Money/crypto transferred correctly on acceptance

#### Test 3: GUI Operations (No Player Names)
- [ ] `/crypto` opens main menu
- [ ] Buy crypto works
- [ ] Sell crypto works
- [ ] Portfolio displays correctly
- [ ] Market prices display correctly
- [ ] Deposit Money works
- [ ] Withdraw Money works

### New Functionality (Player Names with Spaces)

#### Test 4: Player With Spaces - Send Command
```bash
/crypto send "Cool Player" NINJ 5
```
**Expected Results:**
- [ ] Command parses correctly
- [ ] Player "Cool Player" is found
- [ ] Crypto transferred successfully
- [ ] Sender receives: "§a[Crypto] Sent 5.0000 NINJ to Cool Player."
- [ ] Receiver receives: "§a[Crypto] Received 5.0000 NINJ from [sender]."

#### Test 5: Player With Spaces - Offer Command
```bash
/crypto offer "Cool Player" NINJ 5 100
```
**Expected Results:**
- [ ] Command parses correctly
- [ ] Player "Cool Player" is found
- [ ] Offer created successfully
- [ ] Offer ID assigned
- [ ] Target player receives notification
- [ ] Offer appears in `/crypto offers all`

#### Test 6: Player With Multiple Spaces
```bash
/crypto send "Player With Multiple Spaces" NINJ 10
```
**Expected Results:**
- [ ] Command parses correctly
- [ ] Player found
- [ ] Transaction completes successfully

#### Test 7: Quoted Player Name Without Spaces
```bash
/crypto send "PlayerName" NINJ 5
```
**Expected Results:**
- [ ] Works identically to unquoted version
- [ ] No errors
- [ ] Transaction completes successfully

### Money Scoreboard Integration

#### Test 8: Buy Crypto (Player with Spaces)
**Setup:** Player "Cool Player" has $1000 Money
```
1. Player types: /crypto
2. Clicks "Buy Crypto"
3. Selects NINJ
4. Enters quantity: 5
5. Clicks "Buy Now"
```
**Expected Results:**
- [ ] Money deducted from scoreboard correctly
- [ ] Crypto added to holdings
- [ ] Confirmation message displayed
- [ ] Scoreboard shows updated Money value

#### Test 9: Sell Crypto (Player with Spaces)
**Setup:** Player "Cool Player" has 5 NINJ
```
1. Player types: /crypto
2. Clicks "Sell Crypto"
3. Selects NINJ
4. Enters quantity: 3
5. Clicks "Sell Now"
```
**Expected Results:**
- [ ] Money added to scoreboard correctly
- [ ] Crypto deducted from holdings
- [ ] Confirmation message displayed
- [ ] Scoreboard shows updated Money value

#### Test 10: Deposit Money (Player with Spaces)
**Setup:** Player "Cool Player" has 500 internal credits
```
1. Player types: /crypto
2. Clicks "Deposit Money"
3. Enters amount: 500
4. Clicks "Deposit"
```
**Expected Results:**
- [ ] Internal credits deducted: 500 → 0
- [ ] Money added to scoreboard: +500
- [ ] Confirmation message: "§a[Crypto] Deposited 500 credits to Money."
- [ ] Scoreboard shows updated Money value

#### Test 11: Withdraw Money (Player with Spaces)
**Setup:** Player "Cool Player" has $1000 Money
```
1. Player types: /crypto
2. Clicks "Withdraw Money"
3. Enters amount: 300
4. Clicks "Withdraw"
```
**Expected Results:**
- [ ] Money deducted from scoreboard: $1000 → $700
- [ ] Internal credits increased: +300
- [ ] Confirmation message: "§a[Crypto] Withdrew $300 from Money to credits."
- [ ] Scoreboard shows updated Money value

### P2P Trading (Player Names with Spaces)

#### Test 12: Create P2P Offer via GUI (Player with Spaces)
**Setup:** Player "Cool Player" has 10 NINJ
```
1. Player types: /crypto
2. Clicks "P2P Trading"
3. Clicks "Create Offer"
4. Selects NINJ
5. Enters quantity: 5
6. Enters price: 100
7. Enters target: "Another Player"
8. Clicks "Create Offer"
```
**Expected Results:**
- [ ] Offer created successfully
- [ ] Target player "Another Player" receives notification
- [ ] Offer appears in listings

#### Test 13: Accept P2P Offer (Player with Spaces)
**Setup:** Player "Cool Player" has an offer from "Another Player"
```
1. Player "Cool Player" types: /crypto accept 1
```
**Expected Results:**
- [ ] Money deducted from "Cool Player" scoreboard
- [ ] Crypto transferred to "Cool Player"
- [ ] Money added to "Another Player" scoreboard
- [ ] Crypto deducted from "Another Player"
- [ ] Both players receive confirmation messages
- [ ] Offer status changed to "filled"

### Edge Cases

#### Test 14: Player Name Not Found
```bash
/crypto send "Nonexistent Player" NINJ 5
```
**Expected Results:**
- [ ] Error message: "§c[Crypto] Player not found (online required)."
- [ ] No transaction occurs

#### Test 15: Unclosed Quote
```bash
/crypto send "Cool Player NINJ 5
```
**Expected Results:**
- [ ] Parses as: ["send", "Cool Player NINJ 5"]
- [ ] Error: Player not found (because it's looking for "Cool Player NINJ 5")
- [ ] No crash or unexpected behavior

#### Test 16: Empty Quotes
```bash
/crypto send "" NINJ 5
```
**Expected Results:**
- [ ] Error message: "§c[Crypto] Player not found (online required)."
- [ ] No transaction occurs

#### Test 17: Special Characters in Name
```bash
/crypto send "Player@123" NINJ 5
```
**Expected Results:**
- [ ] Works if player exists with that name
- [ ] Error if player doesn't exist
- [ ] No crashes

### Performance Testing

#### Test 18: Multiple Players with Spaces
**Setup:** 5 players online, all with spaces in names
```
1. Each player performs buy/sell operations
2. Each player deposits/withdraws Money
3. Players send crypto to each other
4. Players create P2P offers
```
**Expected Results:**
- [ ] All operations complete successfully
- [ ] No performance degradation
- [ ] No errors in logs
- [ ] All scoreboards update correctly

### Regression Testing

#### Test 19: All Original Commands Still Work
- [ ] `/crypto help` - Displays help
- [ ] `/crypto symbols` - Lists symbols
- [ ] `/crypto price NINJ` - Shows price
- [ ] `/crypto chart NINJ` - Shows chart
- [ ] `/crypto holdings` - Shows holdings
- [ ] `/crypto market buy NINJ 5` - Buys crypto
- [ ] `/crypto market sell NINJ 3` - Sells crypto
- [ ] `/crypto offers` - Lists offers
- [ ] `/crypto offers all` - Lists all offers
- [ ] `/crypto accept 1` - Accepts offer
- [ ] `/crypto cancel 1` - Cancels offer

#### Test 20: Admin Commands
- [ ] `/crypto admin help` - Shows admin help
- [ ] `/crypto admin holdings PlayerName` - Shows player holdings
- [ ] `/crypto admin holdings "Cool Player"` - Shows player with spaces holdings
- [ ] All admin commands work with quoted player names

## Summary Checklist

### Pre-Deployment
- [x] Code compiled without errors
- [x] Unit tests pass
- [x] Build successful
- [x] Documentation complete

### Post-Deployment
- [ ] Plugin loads successfully
- [ ] Backward compatibility verified (Tests 1-3, 19)
- [ ] New functionality works (Tests 4-7)
- [ ] Money scoreboard integration works (Tests 8-11)
- [ ] P2P trading works (Tests 12-13)
- [ ] Edge cases handled (Tests 14-17)
- [ ] Performance acceptable (Test 18)
- [ ] Admin commands work (Test 20)

### Sign-Off
- [ ] All critical tests passed
- [ ] No errors in server logs
- [ ] Players can use plugin normally
- [ ] Player names with spaces work correctly
- [ ] Money scoreboard operations work correctly

---

## Test Results

**Date:** _____________

**Tester:** _____________

**Server Version:** _____________

**Plugin Version:** 3.0.1

**Overall Result:** [ ] PASS  [ ] FAIL

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

**Issues Found:**
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

**Recommendations:**
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

