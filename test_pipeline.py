
import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.Test")

# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

import semantic_analyzer
import validation_agent

def test_pipeline():
    logger.info("🚀 Starting Semantic Tagging Pipeline Verification")

    # 1. Setup paths
    # Use the image I just generated. I need the absolute path.
    # Note: I'll need to fill this in dynamically or pass it as an arg, 
    # but for this script I'll hardcode the known path from previous step or find it.
    # For now, I'll search for the png in the brain dir.
    
    brain_dir = r"C:\Users\petri\.gemini\antigravity\brain\1171e80a-fe6c-4248-9595-596c4e18250c"
    image_path = None
    for file in os.listdir(brain_dir):
        if file.startswith("chinese_garden_render") and file.endswith(".png"):
            image_path = os.path.join(brain_dir, file)
            break
            
    if not image_path:
        logger.error("❌ Could not find test image in brain directory.")
        return

    logger.info(f"📸 Test Image: {image_path}")

    # 2. Run Semantic Analysis
    logger.info("🧠 Running Semantic Analysis (Gemini)...")
    manifest = semantic_analyzer.analyze_world(image_path)
    
    if not manifest:
        logger.error("❌ Semantic Analysis Failed.")
        return

    logger.info("✅ Semantic Analysis Complete.")
    print(manifest)

    # 3. Save Manifest for Validation Agent
    manifest_path = image_path.replace(".png", "_manifest.json")
    semantic_analyzer.save_manifest(manifest, manifest_path)
    
    # 4. Run Validation Agent
    logger.info("🛡️ Running Validation Agent...")
    
    # We won't pass a Jira Key effectively disabling the Jira reporting part 
    # but still testing the logic. Or we can mock it.
    # The run_validation function returns a dict of validation results.
    
    validation_results = validation_agent.run_validation(manifest_path, jira_issue_key=None)
    
    if not validation_results:
        logger.error("❌ Validation Agent returned no results.")
        return

    logger.info("✅ Validation Agent Complete.")
    print(validation_results)
    
    logger.info("🎉 Pipeline Verification Successful!")

if __name__ == "__main__":
    test_pipeline()
