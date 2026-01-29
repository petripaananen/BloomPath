"""Save a screenshot from UE5 to a file."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import base64
from middleware.special_agent import CLIENT

def save_screenshot(output_path: str):
    result = CLIENT.call_tool('screenshot/capture', {})
    content = result.get('content', [])
    
    # Look for image content
    for block in content:
        if block.get('type') == 'image':
            # Base64 encoded image data
            image_data = block.get('data', '')
            if image_data:
                with open(output_path, 'wb') as f:
                    f.write(base64.b64decode(image_data))
                print(f"Screenshot saved to: {output_path}")
                return True
        elif block.get('type') == 'text':
            print(f"Response: {block.get('text')}")
    
    return False

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "cabin_screenshot.png"
    save_screenshot(output)
