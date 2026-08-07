# Changelog - Version 3.0.1

## Release Date
October 27, 2025

## Summary
This release adds support for player names with spaces in the `/crypto send` and `/crypto offer` commands.

## New Features

### Player Names with Spaces Support
- **Feature**: Commands now support player names that contain spaces by using quotes
- **Commands Affected**:
  - `/crypto send <player> <symbol> <qty>`
  - `/crypto offer <player> <symbol> <qty> <price>`

### Usage Examples

#### Before (v3.0.0)
```bash
# This would fail for player "Cool Player"
/crypto send Cool Player NINJ 5
# Would try to send to player "Cool" instead of "Cool Player"
```

#### After (v3.0.1)
```bash
# Now works correctly with quotes
/crypto send "Cool Player" NINJ 5

# Also works for P2P offers
/crypto offer "Cool Player" NINJ 5 100

# Backward compatible - still works without quotes for single-word names
/crypto send PlayerName NINJ 5
/crypto offer PlayerName NINJ 5 100
```

## Technical Changes

### Code Changes
1. **New Method**: `_parse_args(self, tail: str) -> List[str]`
   - Location: `src/endstone_crypto/crypto_market.py` (lines 101-136)
   - Purpose: Parse command arguments with support for quoted strings
   - Features:
     - Handles double-quoted strings
     - Preserves spaces within quotes
     - Backward compatible with unquoted arguments

2. **Updated Method**: `on_command()`
   - Changed from: `parts: List[str] = tail.split() if tail else []`
   - Changed to: `parts: List[str] = self._parse_args(tail) if tail else []`

3. **Version Update**:
   - Plugin version: `3.0.0` → `3.0.1`
   - Version comment updated to reflect new feature

### Documentation Updates
1. **MEMBER_GUIDE.md**
   - Added notes about quoted player names in Trading Commands section
   - Added notes about quoted player names in P2P Commands section
   - Updated Scenario 3 example to use quoted player name

2. **MEMBER_GUIDE_DISCORD.md**
   - Added notes about quoted player names in Trading Commands section
   - Added notes about quoted player names in P2P Commands section
   - Updated Scenario 3 example to use quoted player name

3. **QUICK_START_GUIDE.md**
   - Added notes about quoted player names in Trading Commands section
   - Added notes about quoted player names in P2P Trading Commands section

### Testing
- Created `test_parse_args.py` with comprehensive test cases
- All 9 test cases pass successfully
- Tests cover:
  - Player names with spaces (quoted)
  - Player names without spaces (quoted and unquoted)
  - Player names with multiple spaces
  - Commands without player names
  - Edge cases (empty strings, single words)

## Backward Compatibility

✅ **100% Backward Compatible**
- All existing commands continue to work exactly as before
- Player names without spaces work with or without quotes
- No breaking changes to any functionality
- Only adds new capability (quoted player names)

## Bug Fixes
- Fixed: Player names with spaces could not be used in `/crypto send` command
- Fixed: Player names with spaces could not be used in `/crypto offer` command

## Files Modified
1. `src/endstone_crypto/crypto_market.py` - Core implementation
2. `MEMBER_GUIDE.md` - Documentation update
3. `MEMBER_GUIDE_DISCORD.md` - Documentation update
4. `QUICK_START_GUIDE.md` - Documentation update
5. `pyproject.toml` - Version already at 3.0.1

## Files Added
1. `test_parse_args.py` - Test suite for argument parsing
2. `PLAYER_NAME_SPACES_FIX.md` - Detailed fix documentation
3. `CHANGELOG_v3.0.1.md` - This changelog

## Installation

### For Server Administrators
```bash
# Download the new wheel
# endstone_crypto-3.0.1-py3-none-any.whl

# Install or upgrade
pip install endstone_crypto-3.0.1-py3-none-any.whl --force-reinstall

# Restart your server
```

### For Players
No action required. The update is transparent to players, except they can now use player names with spaces by wrapping them in quotes.

## Known Issues
None

## Future Enhancements
None planned for this release cycle.

## Credits
- Developer: TheN1NJ4LL0
- Framework: Endstone 0.10.7+

## Support
For issues or questions:
1. Check the updated documentation (MEMBER_GUIDE.md, QUICK_START_GUIDE.md)
2. Review PLAYER_NAME_SPACES_FIX.md for detailed technical information
3. Contact server administrators

---

**Full Changelog**: v3.0.0...v3.0.1

