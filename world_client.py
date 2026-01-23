
import os
import time
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger("BloomPath.WorldLabs")

class WorldLabsClient:
    """Client for interacting with the World Labs API."""
    
    BASE_URL = "https://api.worldlabs.ai/marble/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("WORLD_LABS_API_KEY")
        if not self.api_key:
            logger.warning("No World Labs API Key provided.")
            
    def _get_headers(self) -> Dict[str, str]:
        return {
            "WLT-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def generate_world(self, prompt: str, output_path: str) -> Optional[str]:
        """
        Generates a 3D world from a text prompt.
        
        Args:
            prompt: Text description of the world.
            output_path: Local path to save the resulting file.
            
        Returns:
            Path to the saved file if successful, None otherwise.
        """
        if not self.api_key:
            logger.error("Cannot generate world: Missing API Key")
            return None

        # 1. Request Generation
        job_id = None
        try:
            # Current API requires a nested 'world_prompt' structure
            payload = {
                "display_name": f"BloomPath Sprint World - {int(time.time())}",
                "world_prompt": {
                    "type": "text",
                    "text_prompt": prompt
                }
            }
            logger.info(f"Requesting world generation for: '{prompt}'")
            
            response = requests.post(f"{self.BASE_URL}/worlds:generate", json=payload, headers=self._get_headers())
            
            if response.status_code != 200:
                logger.error(f"Generate Request Failed: {response.text}")
                response.raise_for_status()
                
            data = response.json()
            job_id = data.get("operation_id")
            
            if not job_id:
                logger.error("No operation_id returned from World Labs API")
                return None
                
            logger.info(f"Generation job started: {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to start generation: {e}")
            return None

        # 2. Poll for Completion
        status = "IN_PROGRESS"
        result_url = None
        
        # Poll loop (default 5 minutes)
        for _ in range(60):
            time.sleep(5) 
            try:
                check_resp = requests.get(f"{self.BASE_URL}/operations/{job_id}", headers=self._get_headers())
                check_resp.raise_for_status()
                data = check_resp.json()
                
                # Check 'done' boolean
                is_done = data.get("done", False)
                metadata = data.get("metadata", {})
                prog_info = metadata.get("progress", {})
                status_desc = prog_info.get("status", "UNKNOWN")
                
                logger.info(f"Job {job_id} status: {status_desc} (Done: {is_done})")
                
                if is_done:
                    response_obj = data.get("response", {})
                    assets = response_obj.get("assets", {})
                    mesh_info = assets.get("mesh", {})
                    result_url = mesh_info.get("collider_mesh_url") # Using collider mesh as proxy for GLB download
                    
                    if not result_url:
                        # Fallback to other asset types if strictly needed, or error out
                        logger.error("Generation succeeded but no mesh URL found in response")
                        # For debugging, log keys
                        logger.info(f"Available assets: {assets.keys()}")
                    break
                    
            except Exception as e:
                logger.warning(f"Error polling job status: {e}")
        
        if not result_url:
            logger.error("Generation timed out or did not return a valid URL in time")
            return None

        # 3. Download Asset
        try:
            logger.info("Downloading generated asset...")
            asset_resp = requests.get(result_url, stream=True)
            asset_resp.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in asset_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Asset saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download asset: {e}")
            return None
