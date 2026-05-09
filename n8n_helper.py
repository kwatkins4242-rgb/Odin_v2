import requests
import json
import logging

logger = logging.getLogger("odin.n8n")

def trigger_webhook(url: str, payload: dict) -> dict:
    """
    Send data to an n8n webhook URL.
    Returns the response status and data.
    """
    try:
        logger.info(f"Triggering n8n webhook: {url}")
        resp = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        return {
            "success": resp.status_code < 400,
            "status_code": resp.status_code,
            "response": resp.text
        }
    except Exception as e:
        logger.error(f"Webhook trigger failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
