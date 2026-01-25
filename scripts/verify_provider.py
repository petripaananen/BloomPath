import os
import sys
import logging

# Add project root to path so we can import middleware
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from middleware.providers.linear import LinearProvider

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    print("🔌 Initializing LinearProvider...")
    # Credentials should be in environment from .env file (loaded by shell or manually here if needed)
    # in this environment we rely on the shell or .env loading
    
    # Manually load env for this script execution to be safe if not running via full app
    from dotenv import load_dotenv
    load_dotenv()
    
    provider = LinearProvider()
    
    print("🔍 Fetching Active Cycle/Sprint...")
    cycle = provider.get_active_sprint_or_cycle()
    if cycle:
        print(f"✅ Active Cycle: {cycle['name']} (ID: {cycle['id']})")
    else:
        print("ℹ️ No active cycle found (expected for a new project).")

    print("\n🔍 Fetching Issues (by manual query to find our new project issues)...")
    # provider.get_sprint_issues() relies on a cycle. 
    # Let's verify we can get a specific issue we know exists, e.g., WFM-1
    # We need to filter by the user's specific team key if they have one, likely "WFM" based on previous output
    
    # Let's try to fetch WFM-1 directly
    issue_key = "WFM-1" 
    print(f"   Fetching {issue_key}...")
    ticket = provider.get_issue(issue_key)
    
    if ticket:
        print(f"✅ Found Ticket: {ticket.id} - {ticket.title}")
        print(f"   Status: {ticket.status}")
        print(f"   Priority: {ticket.priority}")
        print(f"   Provider: {ticket.provider}")
    else:
        print(f"❌ Could not find {issue_key}. (Note: Key might differ if Team Key is not WFM)")

if __name__ == "__main__":
    main()
