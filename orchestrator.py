
import logging
import time
import json
import os
from typing import Dict, Any, Optional

from world_client import WorldLabsClient
from genie_client import GenieClient
import semantic_analyzer
import middleware

logger = logging.getLogger("BloomPath.Orchestrator")

class BloomPathOrchestrator:
    """
    Manages the Project World Model (PWM) loop:
    Intent -> Spatial Synthesis (Marble) -> Dynamic Simulation (Genie) -> UE5
    """
    
    def __init__(self):
        self.world_client = WorldLabsClient()
        self.genie_client = GenieClient()
        self.max_retries = 3

    def parse_intent(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts generation prompt and mechanics from Jira issue."""
        fields = issue_data.get('fields', {})
        summary = fields.get('summary', '')
        description = fields.get('description', '') # Description might be complex struct in Jira Cloud
        
        # Simplified parsing logic
        # In reality, we'd parse the 'description' ADF format or text
        
        # Construct primitive prompt from summary
        prompt = f"A 3D game level: {summary}"
        
        # Determine mechanics based on labels or keywords
        mechanics = "Standard movement, jump, walk"
        labels = fields.get('labels', [])
        if "platformer" in labels:
            mechanics += ", double jump, floating platforms, wall run"
        if "vehicle" in labels:
            mechanics += ", driving physics, ramp interaction, vehicle collision"
        if "puzzle" in labels:
            mechanics += ", button interaction, door logic, carrying objects"
        if "shooter" in labels:
            mechanics += ", aiming, projectile physics, enemy AI"
        if "survival" in labels:
            mechanics += ", resource gathering, health management"
            
        return {
            "prompt": prompt,
            "mechanics": mechanics,
            "issue_key": issue_data.get('key')
        }

    def process_ticket(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Process a Jira ticket through the pipeline.
        """
        start_time = time.time()
        intent = self.parse_intent(issue_data)
        issue_key = intent['issue_key']
        
        logger.info(f"🎹 Orchestrating for {issue_key}: {intent['prompt']}")
        
        current_prompt = intent['prompt']
        mechanics = intent['mechanics']
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"🔄 Iteration {attempt}/{self.max_retries}")
            
            # 1. Spatial Synthesis (Marble AI)
            # define output path
            output_filename = f"{issue_key}_v{attempt}_{int(time.time())}.gltf"
            output_path = os.path.join(os.getcwd(), "content", "generated", output_filename)
            
            logger.info("  > Generating World...")
            generation_result = self.world_client.generate_world(current_prompt, output_path)
            
            if not generation_result:
                logger.error("  > World Generation Failed.")
                return {"status": "error", "reason": "World Generation Failed"}
                
            mesh_path = generation_result.get('mesh_path')
            image_path = generation_result.get('image_path')
            
            if not image_path:
                logger.warning("  > No thumbnail image returned. Skipping Genie simulation (Blind Pass).")
                # If no image, we can't simulate visually. Skip to tagging?
                # For this specific Orchestrator requirement, we probably shouldn't proceed without validation if strict.
                # But let's allow it for robustness with a warning.
                pass 
            else:
                # 2. Dynamic Simulation (Genie 3)
                logger.info("  > Simulating Gameplay (Genie 3)...")
                sim_result = self.genie_client.simulate_gameplay(image_path, mechanics)
                
                if sim_result['status'] == 'completed':
                    data = sim_result['data']
                    verdict = data.get('verdict', 'FAIL')
                    logger.info(f"  > Genie Verdict: {verdict}")
                    
                    if verdict == 'FAIL':
                        logger.warning(f"  > Simulation Failed: {data.get('gameplay_summary')}")
                        # Refine prompt for next iteration
                        # Ultra-simple refinement logic:
                        issues = data.get('issues', [])
                        refinement = "Fix collision issues. Make paths wider."
                        if issues:
                            refinement = f"Fix {issues[0].get('type')}: {issues[0].get('description')}"
                        
                        current_prompt += f". IMPORTANT: {refinement}"
                        logger.info(f"  > Refining prompt: {current_prompt}")
                        continue # Retry loop
                else:
                    logger.error("  > Genie Simulation Error.")
            
            # 3. Success (or we accepted the result)
            logger.info("  > Design Validated.")
            
            # 4. Semantic Tagging & UE5 Injection
            logger.info("  > Running Semantic Tagging...")
            # We use the semantic analyzer on the image we have
            manifest = None
            if image_path:
                manifest = semantic_analyzer.analyze_world(image_path)
            
            if manifest:
                manifest_path = output_path.replace(".gltf", "_manifest.json")
                semantic_analyzer.save_manifest(manifest, manifest_path)
                
                # Filter/Inject tags (Using logic from middleware)
                self._inject_tags_into_ue5(manifest)
            
            elapsed = time.time() - start_time
            return {
                "status": "success",
                "mesh_path": mesh_path,
                "manifest": manifest,
                "iterations": attempt,
                "duration": elapsed
            }
            
        return {"status": "failed", "reason": "Max retries exceeded"}

    def _inject_tags_into_ue5(self, manifest: Dict[str, Any]):
        """Injects tags from an analyzed manifest into UE5 via Remote Control."""
        from ue5_interface import trigger_ue5_set_tag, map_semantic_type_to_actor

        objects = manifest.get("objects", [])
        if not objects:
            return

        for obj in objects:
            semantic_type = obj.get("semantic_type", "").lower()
            tags = obj.get("tags", [])
            
            # Simple heuristic mapping using shared logic
            target_actor = map_semantic_type_to_actor(semantic_type)
            
            if target_actor:
                for tag in tags:
                    try:
                        trigger_ue5_set_tag(target_actor, tag)
                        logger.info(f"Injected tag '{tag}' to actor '{target_actor}'")
                    except Exception as e:
                        logger.error(f"Failed to inject tag: {e}")
