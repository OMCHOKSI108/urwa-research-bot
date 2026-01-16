"""
Strategy 5: Evidence Capture
Saves failure data for debugging and analysis.
"""

import os
import json
import base64
from datetime import datetime
from typing import Dict, Optional, Any
from loguru import logger


class EvidenceCapture:
    """
    Captures evidence on scraping failures for debugging.
    
    Saves:
    - HTML snapshots
    - Response headers
    - Screenshots (if available)
    - Error details
    - Request context
    """
    
    EVIDENCE_DIR = "app/static/evidence"
    MAX_EVIDENCE_FILES = 100  # Keep last 100 failures
    
    def __init__(self):
        os.makedirs(self.EVIDENCE_DIR, exist_ok=True)
        self.capture_count = 0
    
    def capture(self,
                url: str,
                failure_type: str,
                status_code: Optional[int] = None,
                html_content: str = "",
                headers: Optional[Dict] = None,
                error: Optional[Exception] = None,
                screenshot_base64: Optional[str] = None,
                request_context: Optional[Dict] = None) -> str:
        """
        Capture evidence for a failed scrape.
        
        Args:
            url: URL that failed
            failure_type: Type of failure (e.g., "cloudflare", "captcha", "timeout")
            status_code: HTTP status code
            html_content: Raw HTML content received
            headers: Response headers
            error: Exception if any
            screenshot_base64: Base64 encoded screenshot
            request_context: Additional context (strategy used, retry count, etc.)
            
        Returns:
            Evidence ID for reference
        """
        from urllib.parse import urlparse
        
        # Generate evidence ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = urlparse(url).netloc.replace(".", "_")
        evidence_id = f"{timestamp}_{domain}_{failure_type}"
        
        # Create evidence directory
        evidence_path = os.path.join(self.EVIDENCE_DIR, evidence_id)
        os.makedirs(evidence_path, exist_ok=True)
        
        # Save metadata
        metadata = {
            "evidence_id": evidence_id,
            "url": url,
            "domain": urlparse(url).netloc,
            "failure_type": failure_type,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat(),
            "error": str(error) if error else None,
            "request_context": request_context or {},
            "files": []
        }
        
        # Save HTML content
        if html_content:
            html_file = os.path.join(evidence_path, "response.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            metadata["files"].append("response.html")
            metadata["html_length"] = len(html_content)
        
        # Save headers
        if headers:
            headers_file = os.path.join(evidence_path, "headers.json")
            with open(headers_file, 'w') as f:
                json.dump(dict(headers), f, indent=2, default=str)
            metadata["files"].append("headers.json")
        
        # Save screenshot
        if screenshot_base64:
            try:
                screenshot_file = os.path.join(evidence_path, "screenshot.png")
                with open(screenshot_file, 'wb') as f:
                    f.write(base64.b64decode(screenshot_base64))
                metadata["files"].append("screenshot.png")
            except Exception as e:
                logger.warning(f"[Evidence] Failed to save screenshot: {e}")
        
        # Save metadata
        metadata_file = os.path.join(evidence_path, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.capture_count += 1
        logger.info(f"[Evidence] Captured {evidence_id} ({len(metadata['files'])} files)")
        
        # Cleanup old evidence
        self._cleanup_old_evidence()
        
        return evidence_id
    
    def get_evidence(self, evidence_id: str) -> Optional[Dict]:
        """Retrieve evidence by ID."""
        evidence_path = os.path.join(self.EVIDENCE_DIR, evidence_id)
        metadata_file = os.path.join(evidence_path, "metadata.json")
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None
    
    def list_evidence(self, limit: int = 20, failure_type: Optional[str] = None) -> list:
        """List recent evidence captures."""
        evidence_list = []
        
        if not os.path.exists(self.EVIDENCE_DIR):
            return []
        
        for dirname in sorted(os.listdir(self.EVIDENCE_DIR), reverse=True)[:limit * 2]:
            evidence_path = os.path.join(self.EVIDENCE_DIR, dirname)
            metadata_file = os.path.join(evidence_path, "metadata.json")
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                    if failure_type and metadata.get("failure_type") != failure_type:
                        continue
                    
                    evidence_list.append({
                        "evidence_id": metadata["evidence_id"],
                        "url": metadata["url"],
                        "failure_type": metadata["failure_type"],
                        "timestamp": metadata["timestamp"],
                        "files": metadata["files"]
                    })
                    
                    if len(evidence_list) >= limit:
                        break
        
        return evidence_list
    
    def get_failure_stats(self) -> Dict:
        """Get statistics on captured failures."""
        stats = {
            "total_captures": 0,
            "by_failure_type": {},
            "by_domain": {},
            "recent_failures": []
        }
        
        for evidence in self.list_evidence(limit=100):
            stats["total_captures"] += 1
            
            failure_type = evidence.get("failure_type", "unknown")
            stats["by_failure_type"][failure_type] = stats["by_failure_type"].get(failure_type, 0) + 1
            
            from urllib.parse import urlparse
            domain = urlparse(evidence.get("url", "")).netloc
            stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
        
        stats["recent_failures"] = self.list_evidence(limit=5)
        
        return stats
    
    def _cleanup_old_evidence(self):
        """Remove old evidence to prevent disk fill."""
        if not os.path.exists(self.EVIDENCE_DIR):
            return
        
        evidence_dirs = sorted(os.listdir(self.EVIDENCE_DIR))
        
        while len(evidence_dirs) > self.MAX_EVIDENCE_FILES:
            oldest = evidence_dirs.pop(0)
            oldest_path = os.path.join(self.EVIDENCE_DIR, oldest)
            
            try:
                import shutil
                shutil.rmtree(oldest_path)
                logger.debug(f"[Evidence] Cleaned up old evidence: {oldest}")
            except Exception as e:
                logger.warning(f"[Evidence] Failed to cleanup {oldest}: {e}")
    
    def clear_all(self):
        """Clear all captured evidence."""
        import shutil
        if os.path.exists(self.EVIDENCE_DIR):
            shutil.rmtree(self.EVIDENCE_DIR)
            os.makedirs(self.EVIDENCE_DIR, exist_ok=True)
        self.capture_count = 0
        logger.info("[Evidence] Cleared all captured evidence")


# Singleton instance
evidence_capture = EvidenceCapture()
