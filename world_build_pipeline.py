"""
World Build Pipeline - Orchestrates Linear → World Labs → Gemini → UE5 flow.

This module handles the automatic generation of 3D environments from Linear
issues with attached reference images.
"""

import os
import logging
import tempfile
from typing import Optional, Dict, Any, List

from middleware.models.ticket import UnifiedTicket
from middleware.providers.linear import LinearProvider

logger = logging.getLogger("BloomPath.Pipeline.WorldBuild")


class WorldBuildPipeline:
    """
    End-to-end pipeline for auto-building UE5 environments from Linear issues.
    
    Flow:
    1. Download attachments from Linear issue
    2. Generate 3D world via World Labs API (from images)
    3. Analyze generated world with Gemini Vision
    4. Spawn actors in UE5 based on semantic manifest
    """
    
    def __init__(self, output_dir: str = "generated"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def build_from_ticket(
        self, 
        ticket: UnifiedTicket, 
        provider: LinearProvider
    ) -> Optional[Dict[str, Any]]:
        """
        Execute the full build pipeline for a Linear issue.
        
        Args:
            ticket: The unified ticket object
            provider: LinearProvider instance for API calls
            
        Returns:
            Dict with build results or None on failure
        """
        issue_id = ticket.id
        raw_data = ticket.raw_data or {}
        issue_uuid = raw_data.get("id", issue_id)
        
        logger.info(f"🏗️ Starting build pipeline for {issue_id}")
        
        # 1. Download attachments
        local_images = self._download_attachments(issue_uuid, provider)
        
        if not local_images:
            logger.warning(f"No images found for {issue_id}, using text-only generation")
        
        # 2. Generate world via World Labs
        prompt = f"{ticket.title}. {ticket.description or ''}"
        world_result = self._generate_world(issue_id, prompt, local_images)
        
        if not world_result:
            logger.error(f"World generation failed for {issue_id}")
            return None
        
        # 3. Analyze with Gemini
        manifest = self._analyze_world(world_result.get("image_path"))
        
        # 4. Spawn in UE5 (prefer glTFRuntime if mesh available)
        mesh_path = world_result.get("mesh_path")
        spawn_result = self._spawn_in_ue5(manifest, issue_id, glb_path=mesh_path)
        
        logger.info(f"✅ Build pipeline completed for {issue_id}")
        
        return {
            "issue_id": issue_id,
            "world_result": world_result,
            "manifest": manifest,
            "spawn_result": spawn_result
        }
    
    def _download_attachments(
        self, 
        issue_uuid: str, 
        provider: LinearProvider
    ) -> List[str]:
        """Download all image attachments from a Linear issue."""
        local_paths = []
        
        try:
            attachments = provider.get_issue_attachments(issue_uuid)
            
            for att in attachments:
                url = att.get("url", "")
                att_id = att.get("id", "unknown")
                
                # Check if it's an image
                if any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                    # Determine extension
                    ext = os.path.splitext(url)[1] or ".png"
                    local_path = os.path.join(self.output_dir, f"attachment_{att_id}{ext}")
                    
                    if provider.download_attachment(url, local_path):
                        local_paths.append(local_path)
                        
        except Exception as e:
            logger.error(f"Failed to download attachments: {e}")
        
        logger.info(f"Downloaded {len(local_paths)} image attachments")
        return local_paths
    
    def _generate_world(
        self, 
        issue_id: str, 
        prompt: str, 
        image_paths: List[str]
    ) -> Optional[Dict[str, str]]:
        """Generate 3D world via World Labs API."""
        try:
            from world_client import WorldLabsClient
            client = WorldLabsClient()
            
            output_path = os.path.join(self.output_dir, f"{issue_id}.glb")
            
            if image_paths:
                # Use image-based generation (first image as primary)
                result = client.generate_world_from_image(
                    image_path=image_paths[0],
                    text_prompt=prompt,
                    output_path=output_path
                )
            else:
                # Fall back to text-only generation
                result = client.generate_world(
                    prompt=prompt,
                    output_path=output_path
                )
            
            return result
            
        except Exception as e:
            logger.error(f"World generation error: {e}")
            return None
    
    def _analyze_world(self, image_path: Optional[str]) -> Optional[Dict[str, Any]]:
        """Analyze generated world image with Gemini Vision."""
        if not image_path or not os.path.exists(image_path):
            logger.warning("No image available for semantic analysis")
            return None
        
        try:
            from semantic_analyzer import analyze_world
            manifest = analyze_world(image_path)
            
            if manifest:
                logger.info(f"Semantic analysis found {len(manifest.get('objects', []))} objects")
            
            return manifest
            
        except Exception as e:
            logger.error(f"Semantic analysis error: {e}")
            return None
    
    def _spawn_in_ue5(
        self, 
        manifest: Optional[Dict[str, Any]], 
        tag: str,
        glb_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Spawn UE5 actors - either import full .glb mesh via glTFRuntime,
        or fall back to primitives based on semantic manifest.
        """
        result = {"spawned": 0, "errors": [], "method": "primitives"}
        
        try:
            from middleware.special_agent import CLIENT
            
            # Try glTFRuntime import if we have a .glb file
            if glb_path and os.path.exists(glb_path):
                result["method"] = "gltf_runtime"
                return self._import_via_gltf_runtime(glb_path, tag, CLIENT)
            
            # Fall back to primitive spawning from manifest
            if not manifest:
                logger.warning("No manifest or glb file, skipping UE5 spawn")
                return result
            
            result = self._spawn_primitives_from_manifest(manifest, tag, CLIENT)
            
        except ImportError:
            logger.warning("Special Agent client not available")
            result["errors"].append("Special Agent client not available")
        except Exception as e:
            logger.error(f"UE5 spawn error: {e}")
            result["errors"].append(str(e))
        
        return result

    def _import_via_gltf_runtime(
        self, 
        glb_path: str, 
        tag: str,
        client
    ) -> Dict[str, Any]:
        """Import .glb file using glTFRuntime plugin."""
        result = {"spawned": 0, "errors": [], "method": "gltf_runtime"}
        
        # Convert Windows path to UE5 compatible path
        ue5_path = glb_path.replace("\\", "/")
        
        script = f'''
import unreal

# glTFRuntime import
gltf_runtime = unreal.glTFRuntimeFunctionLibrary

# Load the asset
config = unreal.glTFRuntimeConfig()
config.scene_scale = 100.0  # cm to m conversion

asset = gltf_runtime.gltf_load_asset_from_filename("{ue5_path}", config)

if asset:
    # Get world
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # Spawn actor
    location = unreal.Vector(-400, 300, 92)
    rotation = unreal.Rotator(0, 0, 0)
    
    actor = unreal.glTFRuntimeAssetActor(world)
    actor.set_actor_location(location, False, False)
    
    # Load scene from asset
    actor.load_scene_async(asset, unreal.glTFRuntimeSceneLoadConfig())
    
    # Tag it
    actor.set_actor_label("{tag}_World")
    actor.tags.append("{tag}")
    actor.tags.append("WorldLabsImport")
    
    print(f"Imported glTF: {tag}_World")
else:
    print("ERROR: Failed to load glTF asset")
'''
        try:
            output = client.execute_python(script)
            if "ERROR" not in output:
                result["spawned"] = 1
                logger.info(f"✅ Imported .glb via glTFRuntime: {glb_path}")
            else:
                result["errors"].append(output)
                logger.error(f"glTFRuntime import failed: {output}")
        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"glTFRuntime import error: {e}")
        
        return result

    def _spawn_primitives_from_manifest(
        self, 
        manifest: Dict[str, Any], 
        tag: str,
        client
    ) -> Dict[str, Any]:
        """Spawn UE5 primitives based on semantic manifest (fallback method)."""
        result = {"spawned": 0, "errors": [], "method": "primitives"}
        
        mesh_map = {
            "wall": "/Engine/BasicShapes/Cube",
            "floor": "/Engine/BasicShapes/Cube",
            "ground": "/Engine/BasicShapes/Plane",
            "rock": "/Engine/BasicShapes/Sphere",
            "stone": "/Engine/BasicShapes/Sphere",
            "path": "/Engine/BasicShapes/Plane",
            "water": "/Engine/BasicShapes/Plane",
            "plant": "/Engine/BasicShapes/Cone",
            "tree": "/Engine/BasicShapes/Cone",
            "furniture": "/Engine/BasicShapes/Cube",
            "table": "/Engine/BasicShapes/Cube",
            "chair": "/Engine/BasicShapes/Cube",
            "door": "/Engine/BasicShapes/Cube",
            "window": "/Engine/BasicShapes/Plane",
            "roof": "/Engine/BasicShapes/Cone",
            "fireplace": "/Engine/BasicShapes/Cube",
        }
        
        objects = manifest.get("objects", [])
        base_x, base_y, base_z = -400, 300, 92
        
        for i, obj in enumerate(objects):
            obj_id = obj.get("id", f"obj_{i}")
            semantic_type = obj.get("semantic_type", "unknown").lower()
            mesh_path = mesh_map.get(semantic_type, "/Engine/BasicShapes/Cube")
            
            # Use estimated position if available
            pos = obj.get("estimated_position", {})
            offset_x = {"left": -150, "center": 0, "right": 150}.get(pos.get("x", "center"), (i % 5) * 150)
            offset_y = {"front": -150, "center": 0, "back": 150}.get(pos.get("z", "center"), (i // 5) * 150)
            
            script = f'''
import unreal
actor_class = unreal.StaticMeshActor
location = unreal.Vector({base_x + offset_x}, {base_y + offset_y}, {base_z})
rotation = unreal.Rotator(0, 0, 0)
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)
if actor:
    mesh = unreal.EditorAssetLibrary.load_asset("{mesh_path}")
    if mesh:
        actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_label("{obj_id}")
    actor.tags.append("{tag}")
    actor.tags.append("{semantic_type}")
    print(f"Spawned: {obj_id}")
'''
            try:
                client.execute_python(script)
                result["spawned"] += 1
            except Exception as e:
                result["errors"].append(f"{obj_id}: {str(e)}")
        
        logger.info(f"Spawned {result['spawned']} primitive actors in UE5")
        return result


# Convenience function for direct invocation
def build_from_linear_issue(issue_id: str) -> Optional[Dict[str, Any]]:
    """
    Build 3D environment from a Linear issue by ID.
    
    Usage:
        from world_build_pipeline import build_from_linear_issue
        result = build_from_linear_issue("WFM-8")
    """
    from middleware.providers.linear import LinearProvider
    
    provider = LinearProvider()
    ticket = provider.get_issue(issue_id)
    
    if not ticket:
        logger.error(f"Issue {issue_id} not found")
        return None
    
    pipeline = WorldBuildPipeline()
    return pipeline.build_from_ticket(ticket, provider)
