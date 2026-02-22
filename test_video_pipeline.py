import os
import logging
from middleware.providers.linear import LinearProvider
from orchestrator import BloomPathOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VideoTest")

def main():
    logger.info("Starting Video Processing Test...")
    
    # Initialize providers
    provider = LinearProvider()
    orchestrator = BloomPathOrchestrator()
    
    # 1. Fetch WFM-19
    logger.info("Fetching WFM-19...")
    ticket = provider.get_issue("WFM-19")
    
    if not ticket:
        logger.error("Failed to find WFM-19")
        return
        
    logger.info(f"Found Ticket: {ticket.title}")
    logger.info(f"Attachments Detected: {len(ticket.attachments)}")
    for att in ticket.attachments:
        logger.info(f" - {att.get('title')}: {att.get('url')}")
        
    logger.info(f"Description sample: {ticket.description[:100]}...")
    
    import re
    md_links = re.findall(r'\[([^\]]+)\]\((https://uploads\.linear\.app/[^\)]+)\)', ticket.description)
    logger.info(f"Regex found links: {md_links}")
        
    # 2. Run Pipeline
    logger.info("Starting Pipeline Processing...")
    result = orchestrator.process_ticket(ticket)
    
    logger.info("Pipeline Complete!")
    logger.info(f"Result: {result}")

if __name__ == "__main__":
    main()
