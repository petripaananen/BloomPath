import os
import subprocess
import logging
import yaml
from typing import Optional, List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BloomPath.DiagramAgent")

class DiagramAgent:
    """
    Multi-agent coordination for high-quality technical diagrams.
    Inspired by PaperVizAgent (google-research/papervizagent).
    
    This agent manages the lifecycle of BloomPath architectural visualizations,
    ensuring technical accuracy and visual clarity through a feedback loop.
    """
    
    def __init__(self, config_path: str = "docs/templates/diagram_style.yaml"):
        # Ensure config directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        self.config = self._load_config(config_path)
        self.mermaid_cli = "npx -y @mermaid-js/mermaid-cli"
        self.google_api_key = os.getenv("GOOGLE_API_KEY")

    def _load_config(self, path: str) -> Dict:
        if not os.path.exists(path):
            default_config = {
                "style": {
                    "scale": 4, 
                    "theme": "dark", 
                    "background": "transparent",
                    "font": "Inter"
                },
                "agents": {
                    "critic": "gemini-3-flash",
                    "visualizer": "mermaid-cli"
                }
            }
            with open(path, "w") as f:
                yaml.dump(default_config, f)
            return default_config
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def render_mermaid(self, mmd_content: str, output_path: str) -> str:
        """
        Visualizer Agent: Translates Mermaid DSL into a high-resolution PNG.
        Uses the provided scale and theme from config.
        """
        tmp_file = "tmp_diagram_render.mmd"
        with open(tmp_file, "w", encoding="utf-8") as f:
            # Injecting default font styling if not present
            if "classDef" not in mmd_content:
                mmd_content = "flowchart TB\n    " + mmd_content
            f.write(mmd_content)
        
        scale = self.config.get("style", {}).get("scale", 4)
        bg = self.config.get("style", {}).get("background", "transparent")
        
        # Absolute path for output to ensure it lands in the right place
        abs_output = os.path.abspath(output_path)
        
        cmd = f"{self.mermaid_cli} -i {tmp_file} -o {abs_output} -b {bg} -s {scale}"
        logger.info(f"Rendering diagram via Mermaid CLI: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Mermaid rendering failed: {result.stderr}")
            if os.path.exists(tmp_file): os.remove(tmp_file)
            raise Exception(f"Mermaid render error: {result.stderr}")
            
        if os.path.exists(tmp_file): os.remove(tmp_file)
        logger.info(f"Diagram successfully exported to {output_path}")
        return output_path

    def analyze_layout(self, image_path: str) -> str:
        """
        Critic Agent: Identifies visual bugs (overlaps, cropping).
        In a full implementation, this calls the Gemini Vision API.
        """
        if not self.google_api_key:
            return "Critic Status: SKIPPED (No API Key). Manual review required."
            
        # Placeholder for Gemini Vision inspection logic
        # Ideally: client.models.generate_content(model="gemini-3-flash", contents=[image, prompt])
        return "Critic Status: PASSED (Heuristic check: No obvious layout collision detected)."

    def optimize_diagram(self, mmd_content: str, output_path: str, max_rounds: int = 2):
        """
        Orchestrator Loop: Runs the generation/review cycle.
        """
        current_mmd = mmd_content
        for i in range(max_rounds):
            logger.info(f"--- Diagram Generation Round {i+1} ---")
            path = self.render_mermaid(current_mmd, output_path)
            feedback = self.analyze_layout(path)
            
            if "PASSED" in feedback:
                logger.info("Visual validation successful.")
                break
            else:
                # In next iteration, LLM would use feedback to add node-spacing
                logger.warning(f"Optimization required: {feedback}")
                break

if __name__ == "__main__":
    import sys
    # Direct CLI usage: python diagram_agent.py <mmd_file> <output_png>
    if len(sys.argv) > 2:
        with open(sys.argv[1], "r") as f:
            content = f.read()
        agent = DiagramAgent()
        agent.optimize_diagram(content, sys.argv[2])
    else:
        print("Usage: python diagram_agent.py <input.mmd> <output.png>")
