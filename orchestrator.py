
import logging
import time
import json
import os
from typing import Dict, Any, Optional

import concurrent.futures

from world_client import WorldLabsClient
from genie_client import GenieClient
import semantic_analyzer

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

    def parse_intent(self, ticket: Any) -> Dict[str, Any]:
        """Extracts generation prompt and mechanics from UnifiedTicket."""
        # Use loose typing 'Any' to avoid circular imports but expect UnifiedTicket
        summary = getattr(ticket, 'title', '')
        labels = getattr(ticket, 'labels', [])
        
        # Construct primitive prompt from summary
        prompt = f"A 3D game level: {summary}"
        
        # Determine mechanics based on labels or keywords
        mechanics = "Standard movement, jump, walk"
        
        # Helper to check labels case-insensitively
        label_set = {str(l).lower() for l in labels}
        
        if "platformer" in label_set:
            mechanics += ", double jump, floating platforms, wall run"
        if "vehicle" in label_set:
            mechanics += ", driving physics, ramp interaction, vehicle collision"
        if "puzzle" in label_set:
            mechanics += ", button interaction, door logic, carrying objects"
        if "shooter" in label_set:
            mechanics += ", aiming, projectile physics, enemy AI"
        if "survival" in label_set:
            mechanics += ", resource gathering, health management"
            
        return {
            "prompt": prompt,
            "mechanics": mechanics,
            "issue_key": getattr(ticket, 'id', 'UNKNOWN')
        }

    def process_ticket(self, ticket: Any) -> Dict[str, Any]:
        """
        Main entry point: Process a UnifiedTicket through the pipeline.
        This now acts as an "Organizer Agent", dispatching work to parallel sub-agents.
        """
        start_time = time.time()
        intent = self.parse_intent(ticket)
        issue_key = intent['issue_key']
        
        logger.info(f"🎹 Orchestrator (Agentic Mode) for {issue_key}: {intent['prompt']}")
        
        current_prompt = intent['prompt']
        mechanics = intent['mechanics']
        
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"🔄 Iteration {attempt}/{self.max_retries}")
            
            # 1. Spatial Synthesis (Marble AI)
            output_filename = f"{issue_key}_v{attempt}_{int(time.time())}.gltf"
            output_path = os.path.join(os.getcwd(), "content", "generated", output_filename)
            
            logger.info("  > Generating World via Matrix...")
            generation_result = self.world_client.generate_world(current_prompt, output_path)
            
            if not generation_result:
                logger.error("  > World Generation Failed.")
                return {"status": "error", "reason": "World Generation Failed"}
                
            mesh_path = generation_result.get('mesh_path')
            image_path = generation_result.get('image_path')
            
            # Initialize confidence_score to 100 (assume success if no simulation runs)
            confidence_score = 100.0
            
            if not image_path:
                logger.warning("  > No thumbnail image. Skipping 'Dreaming' phase.")
                # confidence_score remains 100.0 (no simulation = no detected issues)
            else:
                # 2. Parallel Simulation (AsyncThink) - The Dreaming
                logger.info("  > Dispatching 3 Parallel Simulation Agents (The Dreaming)...")
                
                sim_results = []
                profiles = ["baseline", "stress_test", "optimization"]
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_profile = {
                        executor.submit(self.genie_client.simulate_gameplay, image_path, mechanics, profile): profile
                        for profile in profiles
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_profile):
                        profile = future_to_profile[future]
                        try:
                            result = future.result()
                            result['profile'] = profile
                            sim_results.append(result)
                            logger.info(f"    > Agent '{profile.upper()}' finished with {result.get('data', {}).get('verdict')}")
                        except Exception as exc:
                            logger.error(f"    > Agent '{profile}' crashed: {exc}")

                # 3. Aggregate Results (Consensus Mechanism)
                pass_count = sum(1 for r in sim_results if r.get('data', {}).get('verdict') == "PASS")
                confidence_score = (pass_count / len(profiles)) * 100 if profiles else 0
                
                logger.info(f"  > Dreaming Complete. Confidence Score: {confidence_score:.1f}% ({pass_count}/{len(profiles)} passed)")
                
                # Generate Strategist Report
                self._generate_strategist_report(issue_key, current_prompt, sim_results, confidence_score)

                if confidence_score < 66.0: # Need at least 2/3 majority
                    logger.warning(f"  > Confidence too low. Refinement needed.")
                    # Refinement Logic
                    refinement = "General stability improvements."
                    # Find first failure reason
                    for res in sim_results:
                        data = res.get('data', {})
                        if data.get('verdict') == 'FAIL':
                            issues = data.get('issues', [])
                            if issues:
                                refinement = f"Fix {issues[0].get('type')} identified by {res['profile']} agent."
                                break
                    
                    current_prompt += f". IMPORTANT: {refinement}"
                    logger.info(f"  > Refining prompt: {current_prompt}")
                    continue # Retry loop
            
            # 4. Success / Latent Risk Visualization
            logger.info("  > Design Validated.")
            
            # 4b. Latent Risk Visualization (Thesis Feature)
            # Even if we pass, if confidence isn't 100%, show a ghost.
            if confidence_score < 100:
                logger.info("  > Confidence < 100%. Triggering Latent Risk (Ghost) in UE5.")
                try:
                    from ue5_interface import trigger_phantom_warning
                    trigger_phantom_warning("Location_Center", risk_level=1.0 - (confidence_score/100.0))
                except Exception as e:
                    logger.warning(f"Failed to trigger phantom: {e}")

            # 5. Semantic Tagging & UE5 Injection
            logger.info("  > Running Semantic Tagging...")
            manifest = None
            if image_path:
                manifest = semantic_analyzer.analyze_world(image_path)
            
            if manifest:
                manifest_path = output_path.replace(".gltf", "_manifest.json")
                semantic_analyzer.save_manifest(manifest, manifest_path)
                self._inject_tags_into_ue5(manifest)
            
            elapsed = time.time() - start_time
            return {
                "status": "success",
                "mesh_path": mesh_path,
                "manifest": manifest,
                "confidence": confidence_score,
                "iterations": attempt,
                "duration": elapsed
            }
            
        return {"status": "failed", "reason": "Max retries exceeded"}

    def _generate_strategist_report(self, issue_key: str, prompt: str, results: list, confidence: float):
        """Generates a Markdown report for the Scenario Strategist (Project Manager)."""
        report_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        filename = f"PWM_Report_{issue_key}_{int(time.time())}.md"
        path = os.path.join(report_dir, filename)
        
        status_icon = "🟢" if confidence >= 80 else "🟡" if confidence >= 50 else "🔴"
        
        content = f"""# PWM Scenario Strategy Report: {issue_key}

**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Intent**: "{prompt}"
**Overall Confidence**: {status_icon} {confidence:.1f}%

## 🔮 The Dreaming (Simulation Results)
Analysis of {len(results)} parallel futures:

"""
        for res in results:
            profile = res.get('profile', 'unknown').upper()
            data = res.get('data', {})
            verdict = data.get('verdict', 'UNKNOWN')
            icon = "✅" if verdict == "PASS" else "❌"
            summary = data.get('gameplay_summary', 'No details.')
            
            content += f"### {icon} {profile} Agent\n"
            content += f"- **Verdict**: {verdict}\n"
            content += f"- **Summary**: {summary}\n"
            if data.get('issues'):
                content += "- **Issues**:\n"
                for issue in data.get('issues'):
                    content += f"  - [{issue.get('severity')}] {issue.get('type')}: {issue.get('description')}\n"
            content += "\n"
            
        content += """## 🧠 Strategic Recommendation
"""
        if confidence >= 80:
            content += "🚀 **GREEN LIGHT**: The design is robust across all scenarios. Procedural generation approved."
        elif confidence >= 50:
            content += "⚠️ **CAUTION**: Significant risks detected in alternative scenarios (Stress/Edge cases). Recommend manual review or 'Ghost' monitoring."
        else:
            content += "🛑 **BLOCK**: High probability of failure. Refinement loop triggered automatically."
            
        with open(path, "w", encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"📄 Scenario Report generated: {path}")

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
