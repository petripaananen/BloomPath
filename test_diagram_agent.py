import os
import time
import logging
from middleware.diagram_agent import DiagramAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestDiagramAgent")

# Intentionally flawed mermaid code with excessive text and wrong routing
FLAWED_MERMAID = """flowchart TB
    A["Extremely Long Node Description That Will Overlap Stuff With No Line Breaks Allowed"]
    B["Another Very Dense Node About Project Data"]
    C["Core Orchestrator Orchestrating Synchronous Logic"]
    
    subgraph Container 1
        direction LR
        A -->|"HTTP POST (Webhook Payload JSON Object)"| B
    end
    
    B -->|"1. Complex Database Query Executing"| C
    C -.->|"2. Async Background Job Finished Syncing"| A
"""

class MockDiagramAgent(DiagramAgent):
    """
    Subclasses the DiagramAgent to mock the Gemini Vision 'Critic' feedback.
    """
    def __init__(self):
        super().__init__()
        self.mock_generation_attempts = 0

    def analyze_layout(self, image_path: str) -> str:
        """ Simulate Gemini Vision locating layout overlaps. """
        self.mock_generation_attempts += 1
        
        logger.info(f"Mock Critic Agent analyzing {image_path}...")
        time.sleep(1.0) # Simulate API latency
        
        if self.mock_generation_attempts == 1:
            return "Critic Status: FAILED. Overlap detected between node A and B. The text 'Extremely Long Node Description' escapes the boundaries."
        else:
            return "Critic Status: PASSED. No structural overlaps detected after refinement."

def refine_mermaid(original_mmd: str, feedback: str) -> str:
    """ Mock process of an LLM interpreting feedback and rewriting the DSL. """
    logger.info("Mock Refinement Agent parsing feedback and rewriting Mermaid DSL...")
    time.sleep(1.5) # Simulate LLM thinking time
    
    # Returning a "fixed" version
    return """flowchart TB
    A["Node A<br/>Brief Description"]
    B["Project Data"]
    C["Core Orchestrator"]
    
    subgraph Container 1
        A --->|"Webhook JSON"| B
    end
    
    B --->|"Query Exec"| C
    C -.->|"Async Job"| A
"""

def main():
    agent = MockDiagramAgent()
    output_png = "docs/test_render.png"
    
    logger.info("=== Starting WFM-26 Evaluation ===")
    
    start_time = time.time()
    
    # Round 1 (Flawed)
    current_mmd = FLAWED_MERMAID
    logger.info(f"--- Diagram Generation Round 1 ---")
    
    render_start = time.time()
    path = agent.render_mermaid(current_mmd, output_png)
    render_time = time.time() - render_start
    logger.info(f"Mermaid CLI Rendering Time: {render_time:.2f} seconds")
    
    feedback = agent.analyze_layout(path)
    
    if "FAILED" in feedback:
        logger.warning(f"Critic detected issues: {feedback}")
        
        # Refinement Loop
        current_mmd = refine_mermaid(current_mmd, feedback)
        
        logger.info(f"--- Diagram Generation Round 2 ---")
        render_start_2 = time.time()
        path = agent.render_mermaid(current_mmd, output_png)
        render_time_2 = time.time() - render_start_2
        logger.info(f"Mermaid CLI Rendering Time: {render_time_2:.2f} seconds")
        
        feedback = agent.analyze_layout(path)
        if "PASSED" in feedback:
             logger.info("Visual validation successful after refinement!")
            
    total_time = time.time() - start_time
    logger.info(f"=== Evaluation Complete ===")
    logger.info(f"Total Pipeline Time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
