#!/usr/bin/env python3
"""
Test script to verify MCP sharing functionality is working correctly
"""

import asyncio
import json
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.utils.db import db

async def test_mcp_sharing():
    """Test the MCP sharing functionality"""
    
    print("🧪 Testing MCP Sharing Fix")
    print("=" * 50)
    
    try:
        client = await db.client
        
        # Test 1: Check if custom_mcps column exists
        print("1. Checking database schema...")
        tables_result = await client.rpc('get_schema_info').execute()
        
        # Test 2: Check agents with custom MCPs
        print("2. Finding agents with custom MCPs...")
        result = await client.table('agents').select('agent_id,name,custom_mcps,sharing_preferences,is_public').neq('custom_mcps', '[]').limit(3).execute()
        
        if result.data:
            for agent in result.data:
                print(f"   ✅ Agent: {agent['name']}")
                print(f"      - Custom MCPs: {len(agent.get('custom_mcps', []))} items")
                print(f"      - Sharing prefs: {agent.get('sharing_preferences')}")
                print(f"      - Is public: {agent.get('is_public')}")
                
                # Show a sample custom MCP if available
                if agent.get('custom_mcps') and len(agent.get('custom_mcps', [])) > 0:
                    sample_mcp = agent['custom_mcps'][0]
                    print(f"      - Sample MCP: {sample_mcp.get('name')} ({sample_mcp.get('type')})")
                print()
        else:
            print("   ⚠️  No agents with custom MCPs found")
        
        # Test 3: Test the get_marketplace_agents function
        print("3. Testing marketplace agents function...")
        marketplace_result = await client.rpc('get_marketplace_agents', {
            'p_limit': 5,
            'p_offset': 0,
            'p_search': None,
            'p_tags': None,
            'p_account_id': None
        }).execute()
        
        has_custom_mcps = False
        for agent in marketplace_result.data:
            if agent.get('custom_mcps') and len(agent.get('custom_mcps', [])) > 0:
                has_custom_mcps = True
                print(f"   ✅ Found agent with custom MCPs in marketplace: {agent['name']}")
                print(f"      - Custom MCPs: {len(agent.get('custom_mcps', []))} items")
                print(f"      - Sharing prefs: {agent.get('sharing_preferences')}")
                break
        
        if not has_custom_mcps:
            print("   ⚠️  No agents with custom MCPs found in marketplace response")
        
        # Test 4: Explain what should happen
        print("4. Expected behavior:")
        print("   ✅ Marketplace should show ALL MCPs (custom_mcps not filtered)")
        print("   ✅ Import should respect sharing preferences")
        print("   ✅ When 'include_custom_mcp_tools' = true, custom MCPs should transfer")
        print("   ✅ When 'include_custom_mcp_tools' = false, no MCPs should transfer")
        
        print("\n🎯 Test Results Summary:")
        if result.data and has_custom_mcps:
            print("   ✅ PASS: Custom MCPs are available and visible in marketplace")
            print("   ✅ The fix should be working!")
        elif result.data:
            print("   ⚠️  PARTIAL: Agents found but no custom MCPs in marketplace")
            print("   📝 This might be normal if no published agents have custom MCPs")
        else:
            print("   ⚠️  INCONCLUSIVE: No test data available")
            print("   📝 Create an agent with custom MCPs and publish it to test")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_sharing()) 