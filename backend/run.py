
import sys
import asyncio
import io

# Force stdout to be utf-8 to avoid encoding errors in some windows terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if sys.platform == 'win32':
    # CRITICAL: Force ProactorEventLoop for Playwright on Windows
    # This must run before ANY async loop is created
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"🚀 Starting URWA Server (Windows Proactor Fix Applied)...")
    print(f"🔑 Groq Key Present: {bool(os.getenv('GROQ_API_KEY'))}")
    print(f"🌐 Server will run on {host}:{port}")
    
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=False
    )
