from fastapi.testclient import TestClient
import sys
import os

# Ensure backend root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)

def test_health_check():
    """Test standard health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_endpoint():
    """Test root endpoint info"""
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()



def test_smart_scrape_authorized_mock():
    """
    Test authorized request. 
    NOTE: We mock the actual heavy orchestrator call if possible, 
    but for E2E we verify it accepts the key.
    """
    api_key = os.getenv("URWA_API_KEY", "urwa_dev_secret_key")
    payload = {
        "query": "Test Query",
        "use_local_llm": True,
        "output_format": "json"
    }
    # We expect a TaskResponse 
    # BUT: The OrchestratorService inside main.py might try to actually run things 
    # if we don't mock it, but since it's background task, the endpoint should return FAST.
    
    response = client.post(
        "/api/v1/smart_scrape", 
        json=payload,
        headers={"X-API-Key": api_key}
    )
    
    # Assert successful task creation
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "processing"
