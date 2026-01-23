
import os
import sys
import logging
import math
from unittest.mock import MagicMock, patch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.Test.Social")

# Add current dir to path
sys.path.append(os.getcwd())

import middleware

def test_team_member_positioning():
    logger.info("👥 Testing Team Member Positioning Logic...")
    
    # Mock data directly without calling Jira
    # We want to test the distribution logic logic specifically
    
    # Create 10 dummy members
    members = []
    for i in range(10):
        members.append({
            "account_id": f"user_{i}",
            "display_name": f"User {i}",
            "position": {"x": 0, "y": 0, "z": 0} # Placeholder
        })
        
    # Apply positioning logic (simulating what gets done in middleware.get_team_members, 
    # but we might want to extract that logic to test it in isolation if it was a separate function.
    # For now, let's just reverse engineer the logic or copy it to verify intended behavior)
    
    # Replicating the "Spiral" or "Circle" logic we WANT to implement
    # Plan mentioned "Refine position calculation to prevent overlapping"
    
    calculated_members = []
    for i, member in enumerate(members):
        # Spiral Distribution
        # angle = i * golden_angle
        # radius = c * sqrt(i)
        
        golden_angle = 137.508 * (3.14159 / 180) # in radians
        scaling_factor = 300 # distance between avatars
        
        # Or simple circle for small teams, concentric circles for larger?
        # Let's test the Spiral implementation we intend to put in middleware
        
        angle = i * golden_angle
        radius = scaling_factor * math.sqrt(i + 1)
        
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        member["position"] = {"x": round(x, 1), "y": round(y, 1), "z": 0}
        calculated_members.append(member)
        logger.info(f"Member {i}: Pos({x:.1f}, {y:.1f})")

    # Verify no overlaps (roughly)
    min_dist = 100000
    for i in range(len(calculated_members)):
        for j in range(i + 1, len(calculated_members)):
            p1 = calculated_members[i]["position"]
            p2 = calculated_members[j]["position"]
            dist = math.sqrt((p1["x"]-p2["x"])**2 + (p1["y"]-p2["y"])**2)
            if dist < min_dist:
                min_dist = dist
                
    logger.info(f"Minimum distance between avatars: {min_dist:.1f}")
    
    if min_dist < 100:
       logger.warning("⚠️ Avatars might be too close!")
    else:
       logger.info("✅ Avatar distribution looks good.")

if __name__ == "__main__":
    test_team_member_positioning()
