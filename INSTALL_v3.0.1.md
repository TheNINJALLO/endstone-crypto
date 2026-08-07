# Installation Guide - Version 3.0.1

## What's New in v3.0.1?
This version adds support for player names with spaces in `/crypto send` and `/crypto offer` commands.

**New capability:**
```bash
# Now you can send crypto to players with spaces in their names!
/crypto send "Cool Player" NINJ 5
/crypto offer "Cool Player" NINJ 5 100
```

## Quick Install

### Step 1: Download
The wheel file is located at:
```
dist/endstone_crypto-3.0.1-py3-none-any.whl
```

### Step 2: Install
```bash
pip install dist/endstone_crypto-3.0.1-py3-none-any.whl --force-reinstall
```

### Step 3: Restart Server
Restart your Endstone server to load the updated plugin.

### Step 4: Verify
Test the new feature:
```bash
# In-game, try sending to a player with spaces in their name
/crypto send "Player Name" NINJ 5
```

## Detailed Installation Steps

### For Windows

1. **Open PowerShell or Command Prompt**
   ```powershell
   cd C:\path\to\your\server
   ```

2. **Install the updated plugin**
   ```powershell
   pip install C:\path\to\endstone_crypto-3.0.1-py3-none-any.whl --force-reinstall
   ```

3. **Restart your server**
   - Stop the server if running
   - Start the server again

### For Linux/Mac

1. **Open Terminal**
   ```bash
   cd /path/to/your/server
   ```

2. **Install the updated plugin**
   ```bash
   pip install /path/to/endstone_crypto-3.0.1-py3-none-any.whl --force-reinstall
   ```

3. **Restart your server**
   ```bash
   # Stop the server (Ctrl+C if running in foreground)
   # Or use your server management tool
   
   # Start the server again
   ./start_server.sh  # or however you start your server
   ```

## Upgrading from v3.0.0

### No Data Migration Required
This is a minor update with no breaking changes. Your existing data will work perfectly:
- ✅ All player holdings preserved
- ✅ All P2P offers preserved
- ✅ All market prices preserved
- ✅ All configuration preserved

### Backward Compatibility
All existing commands continue to work exactly as before:
```bash
# These still work perfectly
/crypto send PlayerName NINJ 5
/crypto offer PlayerName NINJ 5 100

# And now these work too!
/crypto send "Player Name" NINJ 5
/crypto offer "Player Name" NINJ 5 100
```

## Verification

### Check Plugin Version
After installation, verify the plugin loaded correctly:

1. **Start your server**

2. **Check server logs** for:
   ```
   [INFO] Loading plugin: cryptomarket v3.0.1
   ```

3. **In-game test**:
   ```bash
   /crypto help
   ```
   Should display the help menu without errors.

### Test New Feature
1. **Find a player with spaces in their name** (or ask someone to join with a space in their name)

2. **Try the send command**:
   ```bash
   /crypto send "Player Name" NINJ 5
   ```

3. **Try the offer command**:
   ```bash
   /crypto offer "Player Name" NINJ 5 100
   ```

4. **Verify it works**:
   - No error messages
   - Transaction completes successfully
   - Target player receives the crypto/offer

## Troubleshooting

### Issue: "Player not found"
**Solution**: Make sure you're using quotes around the player name:
```bash
# ❌ Wrong
/crypto send Cool Player NINJ 5

# ✅ Correct
/crypto send "Cool Player" NINJ 5
```

### Issue: Plugin doesn't load
**Solution**: 
1. Check you have Endstone 0.10.7 or higher:
   ```bash
   pip show endstone
   ```

2. Reinstall if needed:
   ```bash
   pip install endstone>=0.10.7 --upgrade
   pip install endstone_crypto-3.0.1-py3-none-any.whl --force-reinstall
   ```

### Issue: Old version still running
**Solution**:
1. Completely stop the server
2. Clear Python cache:
   ```bash
   # Windows
   del /s /q __pycache__
   
   # Linux/Mac
   find . -type d -name __pycache__ -exec rm -rf {} +
   ```
3. Reinstall:
   ```bash
   pip uninstall endstone-crypto -y
   pip install endstone_crypto-3.0.1-py3-none-any.whl
   ```
4. Restart server

## Configuration

No configuration changes are required for this update. The plugin will work with your existing `config.toml` and `holdings.json` files.

## Rollback (If Needed)

If you need to rollback to v3.0.0:

```bash
# Uninstall current version
pip uninstall endstone-crypto -y

# Install previous version
pip install endstone_crypto-3.0.0-py3-none-any.whl

# Restart server
```

Note: v3.0.1 is fully backward compatible, so rollback should not be necessary.

## Support

### Documentation
- **MEMBER_GUIDE.md** - Complete player guide
- **QUICK_START_GUIDE.md** - Quick reference
- **PLAYER_NAME_SPACES_FIX.md** - Technical details about this fix
- **CHANGELOG_v3.0.1.md** - Full changelog

### Getting Help
1. Check the documentation files listed above
2. Review server logs for error messages
3. Test with the verification steps above
4. Contact your server administrator

## Summary

✅ **Easy upgrade** - Just install and restart
✅ **No data loss** - All existing data preserved
✅ **Backward compatible** - All old commands still work
✅ **New feature** - Player names with spaces now supported
✅ **Well tested** - Comprehensive test suite included

**Enjoy the update!**

