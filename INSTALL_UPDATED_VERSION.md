# Installing Updated Crypto Plugin v3.0.0 (Fixed)

## Quick Summary

The Crypto plugin has been updated to fix a dependency issue that was causing PrimeBDS to fail. The new version requires Endstone 0.10.7 or later.

## Step-by-Step Installation

### Step 1: Uninstall Old Version

If you have the old version installed, remove it first:

```bash
pip uninstall endstone-crypto -y
```

### Step 2: Install New Version

Install the updated wheel file:

```bash
pip install dist/endstone_crypto-3.0.0-py3-none-any.whl
```

### Step 3: Verify Installation

Check that everything is installed correctly:

```bash
# Check Endstone version (should be 0.10.7 or higher)
pip show endstone

# Verify endstone.util is available
python -c "from endstone.util import Vector; print('✓ Success')"

# Verify Crypto plugin loads
python -c "from endstone_crypto import CryptoMarket; print('✓ Success')"
```

### Step 4: Restart Server

Restart your Endstone server:

```bash
# Stop the server
# Then start it again
```

## What Changed

**Before (v3.0.0 - original)**:
```toml
dependencies = ["endstone==0.10"]
```

**After (v3.0.0 - fixed)**:
```toml
dependencies = ["endstone>=0.10.7"]
```

## Why This Matters

- The old version allowed Endstone 0.10.0-0.10.6 to be installed
- Those versions don't have the `endstone.util` module
- PrimeBDS needs `endstone.util.Vector`
- The new version ensures Endstone 0.10.7+ is installed
- This fixes the compatibility issue

## Expected Result

After installation and server restart:

✅ Crypto plugin loads successfully  
✅ PrimeBDS loads successfully  
✅ Both plugins work together  
✅ No errors in server logs  

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'endstone.util'"

**Solution**: Ensure Endstone 0.10.7+ is installed:
```bash
pip install --upgrade endstone>=0.10.7
```

### Issue: "endstone-crypto not found"

**Solution**: Make sure you're installing from the correct path:
```bash
pip install /path/to/dist/endstone_crypto-3.0.0-py3-none-any.whl
```

### Issue: Old version still installed

**Solution**: Force reinstall:
```bash
pip uninstall endstone-crypto -y
pip install --force-reinstall dist/endstone_crypto-3.0.0-py3-none-any.whl
```

## Verification Checklist

- [ ] Old version uninstalled
- [ ] New version installed
- [ ] Endstone version is 0.10.7 or higher
- [ ] `endstone.util` module is available
- [ ] Crypto plugin loads without errors
- [ ] Server restarted
- [ ] PrimeBDS loads without errors
- [ ] Both plugins working together

## Support

If you encounter any issues:

1. Check the server logs for error messages
2. Verify Endstone version: `pip show endstone`
3. Verify Crypto plugin: `pip show endstone-crypto`
4. Try reinstalling: `pip install --force-reinstall dist/endstone_crypto-3.0.0-py3-none-any.whl`

## File Location

The updated wheel file is located at:
```
dist/endstone_crypto-3.0.0-py3-none-any.whl
```

---

**Status**: ✅ **READY FOR INSTALLATION**

The updated plugin is ready to deploy on your server!

