# Player Names with Spaces - Fix Summary

## Problem
The crypto plugin previously could not handle player names that contain spaces when using commands like `/crypto send` and `/crypto offer`. This was because the command parser used simple whitespace splitting (`tail.split()`), which would break player names with spaces into multiple arguments.

For example:
- `/crypto send Cool Player NINJ 5` would be parsed as:
  - `['send', 'Cool', 'Player', 'NINJ', '5']` ❌
  - The plugin would try to find a player named "Cool" instead of "Cool Player"

## Solution
Implemented a custom argument parser (`_parse_args`) that supports quoted strings, similar to how shell commands work.

### Technical Changes

#### 1. New `_parse_args` Method
Added a new method in `src/endstone_crypto/crypto_market.py` (lines 101-136):

```python
def _parse_args(self, tail: str) -> List[str]:
    """Parse command arguments, supporting quoted strings for player names with spaces.
    
    Examples:
        'send "Player Name" NINJ 5' -> ['send', 'Player Name', 'NINJ', '5']
        'send PlayerName NINJ 5' -> ['send', 'PlayerName', 'NINJ', '5']
        'offer "Player Name" NINJ 5 100' -> ['offer', 'Player Name', 'NINJ', '5', '100']
    """
```

This parser:
- Handles quoted strings (double quotes `"`)
- Preserves spaces within quotes
- Works with both quoted and unquoted arguments
- Maintains backward compatibility with existing commands

#### 2. Updated Command Handler
Modified the `on_command` method to use the new parser:

**Before:**
```python
parts: List[str] = tail.split() if tail else []
```

**After:**
```python
parts: List[str] = self._parse_args(tail) if tail else []
```

### Usage Examples

#### Sending Crypto to Players with Spaces in Names
```bash
# Player name with spaces - use quotes
/crypto send "Cool Player" NINJ 5

# Player name without spaces - quotes optional
/crypto send PlayerName NINJ 5
/crypto send "PlayerName" NINJ 5  # Also works
```

#### Creating P2P Offers for Players with Spaces in Names
```bash
# Player name with spaces - use quotes
/crypto offer "Cool Player" NINJ 5 100

# Player name without spaces - quotes optional
/crypto offer PlayerName NINJ 5 100
/crypto offer "PlayerName" NINJ 5 100  # Also works
```

### Documentation Updates

Updated the following documentation files to include notes about quoted player names:

1. **MEMBER_GUIDE.md**
   - Added notes in Trading Commands section
   - Added notes in P2P Commands section
   - Updated example in Scenario 3 to use quoted player name

2. **MEMBER_GUIDE_DISCORD.md**
   - Added notes in Trading Commands section
   - Added notes in P2P Commands section
   - Updated example in Scenario 3 to use quoted player name

3. **QUICK_START_GUIDE.md**
   - Added notes in Trading Commands section
   - Added notes in P2P Trading Commands section

### Testing

Created `test_parse_args.py` to verify the parser works correctly with:
- ✓ Player names with spaces in quotes
- ✓ Player names without spaces
- ✓ Player names with multiple spaces
- ✓ Commands without player names
- ✓ Single word commands
- ✓ Empty strings
- ✓ Quoted player names without spaces

All tests pass successfully.

### Backward Compatibility

The fix is **100% backward compatible**:
- Existing commands without quotes continue to work
- Player names without spaces work with or without quotes
- Only player names with spaces require quotes (which didn't work before anyway)

### Commands Affected

The following commands now support player names with spaces:

1. `/crypto send <player> <symbol> <qty>`
   - Example: `/crypto send "Cool Player" NINJ 5`

2. `/crypto offer <player> <symbol> <qty> <price>`
   - Example: `/crypto offer "Cool Player" NINJ 5 100`

### Commands NOT Affected

These commands don't use player names and work as before:
- `/crypto market buy/sell`
- `/crypto price`
- `/crypto chart`
- `/crypto holdings`
- `/crypto offers`
- `/crypto accept`
- `/crypto cancel`
- All admin commands (they use `_resolve_player` which already handles spaces)

## Files Modified

1. `src/endstone_crypto/crypto_market.py` - Added `_parse_args` method and updated `on_command`
2. `MEMBER_GUIDE.md` - Added documentation about quoted player names
3. `MEMBER_GUIDE_DISCORD.md` - Added documentation about quoted player names
4. `QUICK_START_GUIDE.md` - Added documentation about quoted player names
5. `test_parse_args.py` - Created test file to verify parsing logic

## Next Steps

To deploy this fix:

1. Build the new wheel:
   ```bash
   python -m build
   ```

2. Install the updated plugin:
   ```bash
   pip install dist/endstone_crypto-3.0.1-py3-none-any.whl --force-reinstall
   ```

3. Restart the server

4. Test with a player name that has spaces:
   ```bash
   /crypto send "Test Player" NINJ 5
   ```

## Summary

✅ Player names with spaces are now fully supported
✅ Backward compatible with existing commands
✅ Thoroughly tested
✅ Documentation updated
✅ Ready for deployment

