
import logging
import time
import json
import os
from typing import Dict, Any, Optional

from world_client import WorldLabsClient
import semantic_analyzer

logger = logging.getLogger("BloomPath.Orchestrator")

class BloomPathOrchestrator:
    """
    Manages the Project World Model (PWM) loop:
    Intent -> Spatial Synthesis (Marble) -> Semantic Analysis (Gemini) -> UE5
    """
    
    def __init__(self):
        self.world_client = WorldLabsClient()
        self.mechanics_map = self._load_mechanics_config()

    def _load_mechanics_config(self) -> Dict[str, str]:
        """Load mechanics mapping from JSON config."""
        try:
            config_path = os.path.join(os.getcwd(), "config", "mechanics.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load mechanics config: {e}")
        return {}

    def parse_intent(self, ticket: Any) -> Dict[str, Any]:
        """Extracts generation prompt and mechanics from UnifiedTicket."""
        summary = getattr(ticket, 'title', '')
        labels = getattr(ticket, 'labels', [])
        
        prompt = f"A 3D game level: {summary}"
        mechanics_list = ["Standard movement, jump, walk"]
        label_set = {str(l).lower() for l in labels}
        
        for key, value in self.mechanics_map.items():
            if key in label_set:
                mechanics_list.append(value)
            
        if mechanics_list:
            prompt += f" Support mechanics: {', '.join(mechanics_list)}."
            
        return {
            "prompt": prompt,
            "mechanics": ", ".join(mechanics_list),
            "issue_key": getattr(ticket, 'id', 'UNKNOWN')
        }

    def process_ticket(self, ticket: Any) -> Dict[str, Any]:
        """
        Main entry point: Process a UnifiedTicket through the pipeline.
        Intent -> Spatial Synthesis (Marble) -> Semantic Analysis (Gemini) -> UE5
        """
        start_time = time.time()
        intent = self.parse_intent(ticket)
        issue_key = intent['issue_key']
        
        logger.info(f"🎹 Orchestrator (Direct Mode) for {issue_key}: {intent['prompt']}")
        
        current_prompt = intent['prompt']
        
        # 1. Spatial Synthesis (Marble AI)
        output_filename = f"{issue_key}_{int(time.time())}.gltf"
        output_path = os.path.join(os.getcwd(), "content", "generated", output_filename)
        
        logger.info("  > Generating World via Matrix...")
        generation_result = self.world_client.generate_world(current_prompt, output_path)
        
        if not generation_result:
            logger.error("  > World Generation Failed.")
            return {"status": "error", "reason": "World Generation Failed"}
            
        mesh_path = generation_result.get('mesh_path')
        image_path = generation_result.get('image_path')
        
        # 2. Semantic Tagging & UE5 Injection
        logger.info("  > Running Semantic Tagging...")
        manifest = None
        if image_path:
            manifest = semantic_analyzer.analyze_world(image_path)
        
        if manifest:
            manifest_path = output_path.replace(".gltf", "_manifest.json")
            semantic_analyzer.save_manifest(manifest, manifest_path)
            self._inject_tags_into_ue5(manifest)
        
        # 3. Trigger Physical Load in UE5
        if mesh_path and os.path.exists(mesh_path):
            logger.info("  > Commanding UE5 to load the generated world...")
            try:
                from ue5_interface import trigger_ue5_load_level
                trigger_ue5_load_level(mesh_path)
            except Exception as e:
                logger.error(f"Failed to trigger UE5 load: {e}")
        
        elapsed = time.time() - start_time
        return {
            "status": "success",
            "mesh_path": mesh_path,
            "manifest": manifest,
            "duration": elapsed
        }

    def _inject_tags_into_ue5(self, manifest: Dict[str, Any]):
        """Injects tags from an analyzed manifest into UE5 via Remote Control."""
        from ue5_interface import trigger_ue5_set_tag, map_semantic_type_to_actor

        objects = manifest.get("objects", [])
        if not objects:
            return

        for obj in objects:
            semantic_type = obj.get("semantic_type", "").lower()
            tags = obj.get("tags", [])
            target_actor = map_semantic_type_to_actor(semantic_type)
            
            if target_actor:
                for tag in tags:
                    try:
                        trigger_ue5_set_tag(target_actor, tag)
                        logger.info(f"Injected tag '{tag}' to actor '{target_actor}'")
                    except Exception as e:
                        logger.error(f"Failed to inject tag: {e}")

    def dream_scenario(
        self,
        scenario_type: str,
        sprint_data: dict,
        params: dict = None,
        visualize: bool = True
    ) -> dict:
        """
        Run a what-if simulation through the Dreaming Engine.

        Args:
            scenario_type: 'resource_stress', 'scope_creep', or 'priority_shift'
            sprint_data: Current sprint state dict
            params: Optional overrides for scenario defaults
            visualize: If True, send ghost overlay to UE5

        Returns:
            DreamResult as dict with projected outcomes
        """
        from dreaming_engine import dreaming_engine
        from dataclasses import asdict

        logger.info(f"🌙 Orchestrator: Dreaming '{scenario_type}'...")

        result = dreaming_engine.dream(scenario_type, sprint_data, params)

        if visualize:
            viz = dreaming_engine.visualize_dream(result)
            logger.info(f"🌙 Ghost visualization: {viz}")

        return asdict(result)
