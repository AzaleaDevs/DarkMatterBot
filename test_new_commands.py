"""
Test script to verify database functions for the new command system.
This script tests all the new database functions without requiring Discord.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from hola_db import is_user_registered, register_user, get_user_data
from db_utils import (
    get_user_inventory,
    get_user_joints_paginated,
    update_user_currency,
    decrement_cali_pack,
    get_random_joint_by_rarity,
    get_user_cali_packs
)

async def test_database_functions():
    """Test all database functions"""
    print("=" * 60)
    print("Testing Database Functions")
    print("=" * 60)
    
    # Test user ID (use a test ID)
    test_user_id = 999999999
    test_username = "TestUser"
    
    # Test 1: Check if user is registered (should be False initially)
    print("\n1. Testing is_user_registered...")
    is_registered = await is_user_registered(test_user_id)
    print(f"   User {test_user_id} registered: {is_registered}")
    
    # Test 2: Register user if not registered
    if not is_registered:
        print("\n2. Testing register_user...")
        await register_user(test_user_id, test_username)
        print(f"   Registered user {test_user_id} with name {test_username}")
        
        # Verify registration
        is_registered = await is_user_registered(test_user_id)
        print(f"   Verification - User registered: {is_registered}")
    
    # Test 3: Get user data
    print("\n3. Testing get_user_data...")
    user_data = await get_user_data(test_user_id)
    if user_data:
        print(f"   User data: ID={user_data['id']}, Name={user_data['nombre']}")
    else:
        print("   No user data found")
    
    # Test 4: Get user inventory
    print("\n4. Testing get_user_inventory...")
    inventory = await get_user_inventory(test_user_id)
    if inventory:
        print(f"   Inventory:")
        print(f"     Euros: {inventory['euros']}")
        print(f"     Kogos: {inventory['kogos']}")
        print(f"     Cali Park: {inventory['cali_park']}")
        print(f"     Cali DX: {inventory['cali_dx']}")
        print(f"     Cali Semsem: {inventory['cali_semsem']}")
    else:
        print("   No inventory found")
    
    # Test 5: Get user cali packs
    print("\n5. Testing get_user_cali_packs...")
    packs = await get_user_cali_packs(test_user_id)
    if packs:
        print(f"   Cali Packs: {packs}")
    else:
        print("   No packs found")
    
    # Test 6: Update user currency
    print("\n6. Testing update_user_currency...")
    await update_user_currency(test_user_id, euros=5, kogos=20)
    print("   Added 5 euros and 20 kogos")
    
    # Verify update
    inventory = await get_user_inventory(test_user_id)
    if inventory:
        print(f"   Updated Euros: {inventory['euros']}")
        print(f"   Updated Kogos: {inventory['kogos']}")
    
    # Test 7: Get user joints (paginated)
    print("\n7. Testing get_user_joints_paginated...")
    joints, total = await get_user_joints_paginated(test_user_id, offset=0, limit=25)
    print(f"   Total joints owned: {total}")
    if joints:
        print(f"   First page joints:")
        for name, cantidad in joints[:5]:  # Show first 5
            print(f"     - {name} x{cantidad}")
    else:
        print("   No joints owned yet")
    
    # Test 8: Get random joint by rarity
    print("\n8. Testing get_random_joint_by_rarity...")
    for rarity in [1, 2, 3, 4]:
        joint = await get_random_joint_by_rarity('PAR', rarity)
        if joint:
            rarity_names = {1: "Común", 2: "Raro", 3: "Épico", 4: "Legendario"}
            print(f"   Rarity {rarity} ({rarity_names[rarity]}): {joint['nombre']}")
        else:
            print(f"   Rarity {rarity}: No joint found")
    
    # Test 9: Decrement cali pack (if user has any)
    print("\n9. Testing decrement_cali_pack...")
    packs_before = await get_user_cali_packs(test_user_id)
    if packs_before and packs_before['cali_park'] > 0:
        success = await decrement_cali_pack(test_user_id, 'cali_park')
        print(f"   Decrement cali_park: {success}")
        packs_after = await get_user_cali_packs(test_user_id)
        print(f"   Before: {packs_before['cali_park']}, After: {packs_after['cali_park']}")
    else:
        print("   User has no cali_park packs to decrement")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_database_functions())
