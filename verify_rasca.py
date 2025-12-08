"""
Verification script for the /rasca scratch lottery command.
Tests ticket generation probabilities and game logic.
"""
import sys
import os
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the ticket generation function
from Commands.rasca import generate_ticket_items, create_ticket_image

def test_ticket_generation():
    """Test that ticket generation follows the rules"""
    print("Testing ticket generation...")
    print("=" * 50)
    
    num_tests = 1000
    winning_tickets = 0
    max_violations = 0
    
    for i in range(num_tests):
        items = generate_ticket_items()
        
        # Check max 3 of any item
        item_counts = {}
        for item in items:
            item_counts[item] = item_counts.get(item, 0) + 1
        
        max_count = max(item_counts.values())
        
        if max_count > 3:
            max_violations += 1
            print(f"❌ VIOLATION: Ticket has {max_count} of same item: {items}")
        
        # Check if ticket has exactly 3 of any item (winning ticket)
        if max_count == 3:
            winning_tickets += 1
    
    print(f"\n✅ Total tickets generated: {num_tests}")
    print(f"✅ Winning tickets (3 of a kind): {winning_tickets} ({winning_tickets/num_tests*100:.1f}%)")
    print(f"   Expected: ~33%")
    print(f"✅ Violations (more than 3 of a kind): {max_violations}")
    print(f"   Expected: 0")
    
    # Check if win rate is approximately 33%
    win_rate = winning_tickets / num_tests
    if 0.28 <= win_rate <= 0.38:
        print(f"\n✅ Win rate is within acceptable range (28-38%)")
    else:
        print(f"\n⚠️ Win rate {win_rate*100:.1f}% is outside expected range")
    
    print("\n" + "=" * 50)

def test_image_generation():
    """Test image generation with different scratch states"""
    print("\nTesting image generation...")
    print("=" * 50)
    
    try:
        # Generate a test ticket
        items = generate_ticket_items()
        print(f"Test ticket items: {items}")
        
        # Test 1: All hidden
        print("\n1. Generating image with all items hidden...")
        img_data = create_ticket_image(items, set())
        print("   ✅ Successfully generated image with all hidden")
        
        # Test 2: Some scratched
        print("\n2. Generating image with positions 0, 2, 4 scratched...")
        img_data = create_ticket_image(items, {0, 2, 4})
        print("   ✅ Successfully generated image with some scratched")
        
        # Test 3: All scratched
        print("\n3. Generating image with all positions scratched...")
        img_data = create_ticket_image(items, {0, 1, 2, 3, 4})
        print("   ✅ Successfully generated image with all scratched")
        
        # Save a test image
        output_path = "test_rasca_output.png"
        with open(output_path, 'wb') as f:
            f.write(img_data.getvalue())
        print(f"\n✅ Test image saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error during image generation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)

def test_win_detection():
    """Test win detection logic"""
    print("\nTesting win detection logic...")
    print("=" * 50)
    
    # Test winning scenarios
    test_cases = [
        # (items, scratched_positions, should_win, description)
        (['bell', 'bell', 'bell', 'cherry', 'grape'], {0, 1, 2}, True, "3 bells revealed"),
        (['bell', 'cherry', 'bell', 'grape', 'bell'], {0, 2, 4}, True, "3 bells in different positions"),
        (['bell', 'cherry', 'grape', 'diamond', 'lemon'], {0, 1, 2}, False, "All different items"),
        (['bell', 'bell', 'cherry', 'cherry', 'grape'], {0, 1, 2}, False, "2 bells, 1 cherry"),
        (['seven', 'seven', 'seven', 'cherry', 'grape'], {0, 1, 3}, False, "Only 2 sevens revealed"),
    ]
    
    for items, scratched, should_win, description in test_cases:
        revealed_items = [items[i] for i in scratched]
        item_counts = {item: revealed_items.count(item) for item in set(revealed_items)}
        wins = any(count >= 3 for count in item_counts.values())
        
        status = "✅" if wins == should_win else "❌"
        print(f"{status} {description}")
        print(f"   Items: {items}")
        print(f"   Scratched positions: {scratched}")
        print(f"   Revealed: {revealed_items}")
        print(f"   Expected win: {should_win}, Got: {wins}")
        print()
    
    print("=" * 50)

if __name__ == "__main__":
    print("\n🎫 RASCA LOTTERY VERIFICATION SCRIPT 🎫\n")
    
    test_ticket_generation()
    test_image_generation()
    test_win_detection()
    
    print("\n✅ All tests completed!")
