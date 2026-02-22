"""
UI routes for BloomPath middleware.

Serves the Web UI Control Hub used by the Scenario Strategist.
"""

import os
import logging
from flask import Blueprint, render_template, current_app

logger = logging.getLogger("BloomPath.Routes.UI")

# We need to explicitly point the Blueprint to our templates folder.
# By default, Flask looks in the `templates` folder alongside the app.py execution path.
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
ui_bp = Blueprint('ui', __name__, template_folder=template_dir)

@ui_bp.route('/hub', methods=['GET'])
def control_hub():
    """Render the main Control Hub dashboard."""
    try:
        return render_template('control_hub.html')
    except Exception as e:
        logger.error(f"Failed to render Control Hub: {e}")
        return f"Error loading Control Hub: {str(e)}", 500
