#!/usr/bin/env python3
"""Test script to verify the _parse_args function handles player names with spaces correctly."""

def parse_args(tail: str):
    """Parse command arguments, supporting quoted strings for player names with spaces.
    
    Examples:
        'send "Player Name" NINJ 5' -> ['send', 'Player Name', 'NINJ', '5']
        'send PlayerName NINJ 5' -> ['send', 'PlayerName', 'NINJ', '5']
        'offer "Player Name" NINJ 5 100' -> ['offer', 'Player Name', 'NINJ', '5', '100']
    """
    parts = []
    current = []
    in_quotes = False
    i = 0
    
    while i < len(tail):
        char = tail[i]
        
        if char == '"':
            in_quotes = not in_quotes
            i += 1
            continue
        
        if char == ' ' and not in_quotes:
            if current:
                parts.append(''.join(current))
                current = []
            i += 1
            continue
        
        current.append(char)
        i += 1
    
    if current:
        parts.append(''.join(current))
    
    return parts


def test_parse_args():
    """Test the parse_args function with various inputs."""
    
    test_cases = [
        # (input, expected_output, description)
        ('send "Player Name" NINJ 5', ['send', 'Player Name', 'NINJ', '5'], 
         'Player name with spaces in quotes'),
        
        ('send PlayerName NINJ 5', ['send', 'PlayerName', 'NINJ', '5'], 
         'Player name without spaces'),
        
        ('offer "Cool Player" NINJ 5 100', ['offer', 'Cool Player', 'NINJ', '5', '100'], 
         'Offer with player name with spaces'),
        
        ('offer PlayerName NINJ 5 100', ['offer', 'PlayerName', 'NINJ', '5', '100'], 
         'Offer with player name without spaces'),
        
        ('send "Player With Multiple Spaces" NINJ 10', 
         ['send', 'Player With Multiple Spaces', 'NINJ', '10'], 
         'Player name with multiple spaces'),
        
        ('market buy NINJ 5', ['market', 'buy', 'NINJ', '5'], 
         'Command without player name'),
        
        ('help', ['help'], 
         'Single word command'),
        
        ('', [], 
         'Empty string'),
        
        ('send "Player" NINJ 5', ['send', 'Player', 'NINJ', '5'], 
         'Quoted player name without spaces'),
    ]
    
    print("Testing _parse_args function...\n")
    
    all_passed = True
    for i, (input_str, expected, description) in enumerate(test_cases, 1):
        result = parse_args(input_str)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"Test {i}: {status}")
        print(f"  Description: {description}")
        print(f"  Input:    '{input_str}'")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        if not passed:
            print(f"  ERROR: Mismatch!")
        print()
    
    if all_passed:
        print("=" * 60)
        print("All tests PASSED! ✓")
        print("=" * 60)
    else:
        print("=" * 60)
        print("Some tests FAILED! ✗")
        print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = test_parse_args()
    exit(0 if success else 1)

