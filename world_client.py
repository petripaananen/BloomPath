
import os
import time
import logging
import base64
import requests
from typing import Optional, Dict, Any, List

logger = logging.getLogger("BloomPath.Client.WorldLabs")

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

    def generate_world(self, prompt: str, output_path: str) -> Optional[Dict[str, str]]:
        """
        Generates a 3D world from a text prompt.
        
        Args:
            prompt: Text description of the world.
            output_path: Local path to save the resulting file.
            
        Returns:
            Dict with 'mesh_path' and 'image_path' if successful, None otherwise.
        """
        if not self.api_key:
            logger.error("Cannot generate world: Missing API Key")
            return None

        # 1. Request Generation
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

        # 2. Poll and Download
        return self._poll_and_download(job_id, output_path)

    def _upload_media_asset(self, image_path: str) -> Optional[str]:
        """
        Upload a local image to World Labs and return the media_asset_id.
        
        Per API docs: POST /marble/v1/media-assets:prepare_upload, then PUT to signed URL.
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Determine file extension
        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            logger.error(f"Unsupported image format: {ext}")
            return None
        
        file_name = os.path.basename(image_path)
        
        try:
            # 1. Prepare upload
            payload = {
                "file_name": file_name,
                "kind": "image",
                "extension": ext if ext != "jpeg" else "jpg"
            }
            
            resp = requests.post(
                f"{self.BASE_URL}/media-assets:prepare_upload",
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            
            media_asset = data.get("media_asset", {})
            upload_info = data.get("upload_info", {})
            media_asset_id = media_asset.get("id")
            upload_url = upload_info.get("upload_url")
            required_headers = upload_info.get("required_headers", {})
            
            if not media_asset_id or not upload_url:
                logger.error("Failed to get upload URL from World Labs")
                return None
            
            # 2. Upload the file
            with open(image_path, "rb") as f:
                file_data = f.read()
            
            upload_resp = requests.put(
                upload_url,
                data=file_data,
                headers=required_headers,
                timeout=120
            )
            upload_resp.raise_for_status()
            
            logger.info(f"✅ Uploaded {file_name} -> media_asset_id: {media_asset_id}")
            return media_asset_id
            
        except Exception as e:
            logger.error(f"Failed to upload media asset: {e}")
            return None

    def generate_world_from_image(
        self, 
        image_path: str, 
        text_prompt: str,
        output_path: str
    ) -> Optional[Dict[str, str]]:
        """
        Generates a 3D world from an image and optional text prompt.
        
        Args:
            image_path: Path to a local image file (jpg, png, webp).
            text_prompt: Additional text description to guide generation.
            output_path: Local path to save the resulting mesh file.
            
        Returns:
            Dict with 'mesh_path' and 'image_path' if successful, None otherwise.
        """
        if not self.api_key:
            logger.error("Cannot generate world: Missing API Key")
            return None
        
        # Upload the image first
        media_asset_id = self._upload_media_asset(image_path)
        if not media_asset_id:
            return None
        
        # Request generation with image prompt
        try:
            payload = {
                "display_name": f"BloomPath Image World - {int(time.time())}",
                "world_prompt": {
                    "type": "image",
                    "image_prompt": {
                        "source": "media_asset",
                        "media_asset_id": media_asset_id
                    },
                    "text_prompt": text_prompt
                }
            }
            
            logger.info(f"Requesting world generation from image: '{os.path.basename(image_path)}'")
            
            response = requests.post(
                f"{self.BASE_URL}/worlds:generate",
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Generate Request Failed: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            job_id = data.get("operation_id")
            
            if not job_id:
                logger.error("No operation_id returned from World Labs API")
                return None
            
            logger.info(f"Image generation job started: {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to start image generation: {e}")
            return None
        
        # Use the same polling and download logic
        return self._poll_and_download(job_id, output_path)

    def generate_world_from_url(
        self, 
        image_url: str, 
        text_prompt: str,
        output_path: str
    ) -> Optional[Dict[str, str]]:
        """
        Generates a 3D world from an image URL.
        
        Args:
            image_url: Public URL to an image.
            text_prompt: Additional text description.
            output_path: Local path to save the resulting mesh file.
        """
        if not self.api_key:
            logger.error("Cannot generate world: Missing API Key")
            return None
        
        try:
            payload = {
                "display_name": f"BloomPath URL World - {int(time.time())}",
                "world_prompt": {
                    "type": "image",
                    "image_prompt": {
                        "source": "uri",
                        "uri": image_url
                    },
                    "text_prompt": text_prompt
                }
            }
            
            logger.info(f"Requesting world generation from URL: '{image_url}'")
            
            response = requests.post(
                f"{self.BASE_URL}/worlds:generate",
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Generate Request Failed: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            job_id = data.get("operation_id")
            
            if not job_id:
                logger.error("No operation_id returned")
                return None
            
            logger.info(f"URL generation job started: {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to start URL generation: {e}")
            return None
        
        return self._poll_and_download(job_id, output_path)

    def _poll_and_download(self, job_id: str, output_path: str) -> Optional[Dict[str, str]]:
        """Common polling and download logic for all generation types."""
        result_url = None
        thumbnail_url = None
        
        # Poll loop (default 5 minutes)
        for _ in range(60):
            time.sleep(5)
            try:
                check_resp = requests.get(
                    f"{self.BASE_URL}/operations/{job_id}",
                    headers=self._get_headers(),
                    timeout=30
                )
                check_resp.raise_for_status()
                data = check_resp.json()
                
                is_done = data.get("done", False)
                metadata = data.get("metadata", {})
                prog_info = metadata.get("progress", {})
                status_desc = prog_info.get("status", "UNKNOWN")
                
                logger.info(f"Job {job_id} status: {status_desc} (Done: {is_done})")
                
                if is_done:
                    response_obj = data.get("response", {})
                    assets = response_obj.get("assets", {})
                    
                    # Get mesh URL
                    mesh_info = assets.get("mesh", {})
                    result_url = mesh_info.get("collider_mesh_url")
                    
                    # Get thumbnail
                    thumbnail_url = assets.get("thumbnail_url")
                    break
                    
            except Exception as e:
                logger.warning(f"Error polling job status: {e}")
        
        if not result_url:
            logger.error("Generation timed out or no mesh URL returned")
            return None
        
        result_paths = {}
        
        # Download mesh
        try:
            logger.info("Downloading generated mesh...")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            asset_resp = requests.get(result_url, stream=True, timeout=120)
            asset_resp.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in asset_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Mesh saved to {output_path}")
            result_paths["mesh_path"] = output_path
            
        except Exception as e:
            logger.error(f"Failed to download mesh: {e}")
            return None
        
        # Download thumbnail
        if thumbnail_url:
            try:
                img_path = output_path.replace(".gltf", ".png").replace(".glb", ".png")
                logger.info(f"Downloading thumbnail to {img_path}...")
                
                img_resp = requests.get(thumbnail_url, stream=True, timeout=60)
                img_resp.raise_for_status()
                
                with open(img_path, 'wb') as f:
                    for chunk in img_resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                result_paths["image_path"] = img_path
            except Exception as e:
                logger.warning(f"Failed to download thumbnail: {e}")
        
        return result_paths

