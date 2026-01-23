"""Semantic Analyzer - Uses Gemini vision to analyze World Labs renders.

This module takes an image of a generated 3D world and identifies objects
with their game-relevant properties (navigation, physics, tags).
"""

import os
import json
import logging
import base64
from typing import Optional, Dict, Any, List

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("BloomPath.SemanticAnalyzer")

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


ANALYSIS_PROMPT = """You are a game development AI assistant. Analyze this 3D rendered scene and identify distinct objects.

For each object you can identify, provide:
1. semantic_type: What is it? (e.g., rock, wall, path, water, plant, bench, lantern, gate)
2. tags: Game-relevant tags (e.g., Walkable, Obstacle, Climbable, Interactable, Decorative)
3. physics: 
   - friction: 0.0 (ice) to 1.0 (rough stone)
   - mass_category: light/medium/heavy/static
   - destructible: true/false

Focus on objects relevant to gameplay and navigation.
If this is a Chinese garden scene, look for: walls, paths, water features, rocks, plants, gates, bridges, lanterns.

Return ONLY valid JSON in this format:
{
  "scene_description": "Brief description of the scene",
  "objects": [
    {
      "id": "obj_001",
      "semantic_type": "stone_path",
      "tags": ["Walkable", "SoundFootstep_Stone"],
      "physics": {"friction": 0.7, "mass_category": "static", "destructible": false}
    }
  ]
}
"""


def encode_image_base64(image_path: str) -> Optional[str]:
    """Encode an image file to base64 string."""
    try:
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encode image: {e}")
        return None


def analyze_world(image_path: str) -> Optional[Dict[str, Any]]:
    """
    Analyze a World Labs render using Gemini vision.
    
    Args:
        image_path: Path to the rendered image (PNG/JPG)
        
    Returns:
        World Manifest dict or None on failure
    """
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not configured")
        return None
        
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return None
    
    # Encode image
    image_data = encode_image_base64(image_path)
    if not image_data:
        return None
    
    # Determine MIME type
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/png" if ext == ".png" else "image/jpeg"
    
    # Build Gemini request
    payload = {
        "contents": [{
            "parts": [
                {"text": ANALYSIS_PROMPT},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_data
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048
        }
    }
    
    headers = {"Content-Type": "application/json"}
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    
    try:
        logger.info(f"Analyzing image: {image_path}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract text from response
        candidates = result.get("candidates", [])
        if not candidates:
            logger.error("No candidates in Gemini response")
            return None
            
        text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Parse JSON from response (may be wrapped in markdown)
        json_str = text_content.strip()
        if json_str.startswith("```"):
            # Remove markdown code block
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1])
        
        manifest = json.loads(json_str)
        logger.info(f"✅ Identified {len(manifest.get('objects', []))} objects")
        return manifest
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.debug(f"Raw response: {text_content[:500]}")
        return None
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None


def save_manifest(manifest: Dict[str, Any], output_path: str) -> bool:
    """Save manifest to JSON file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest saved: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save manifest: {e}")
        return False
