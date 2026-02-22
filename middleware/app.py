"""
Flask application factory for BloomPath middleware.

This module creates and configures the Flask application with
all routes and extensions.
"""

import os
import logging
from flask import Flask

from middleware.routes import webhooks_bp, api_bp, ui_bp


def create_app(config: dict = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration overrides
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.update({
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
    })
    
    if config:
        app.config.update(config)
    
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Register blueprints
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(ui_bp)
    
    # Legacy route compatibility (redirect /webhook to /webhooks/jira)
    @app.route('/webhook', methods=['POST'])
    def legacy_webhook():
        """Legacy endpoint for backward compatibility."""
        from flask import request
        from middleware.routes.webhooks import jira_webhook
        return jira_webhook()
    
    return app


# For running directly: python -m middleware.app
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    🌱 BloomPath Middleware                    ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  Webhook Endpoints:                                           ║
    ║    • POST /webhooks/jira   - Jira webhooks                    ║
    ║    • POST /webhooks/linear - Linear webhooks                  ║
    ║    • POST /webhook         - Legacy (redirects to Jira)       ║
    ║                                                               ║
    ║  API Endpoints:                                               ║
    ║    • GET  /health          - Health check                     ║
    ║    • GET  /sprint_status   - Sprint/Cycle health              ║
    ║    • POST /complete_task   - UE5 → Done transition            ║
    ║    • GET  /team_members    - Team member list                 ║
    ║    • GET  /dependencies/<id> - Issue dependencies             ║
    ║    • GET  /hub               - AI Scenarios Control Hub       ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'false').lower() == 'true')
