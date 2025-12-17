import uvicorn
import sys
import os
from pyngrok import ngrok, conf
from app.config import settings

def run_server():
    """Chạy FastAPI server"""
    print("\n" + "="*50)
    print(" Starting History Chat & Quiz Proxy Server...")
    print(f" Environment: {settings.environment}")
    print(f" Server: http://{settings.server_host}:{settings.server_port}")
    print(f" API Docs: http://localhost:{settings.server_port}/docs")
    
    if settings.chat_worker_urls:
        print(f" Chat Workers: {len(settings.chat_worker_urls)} URLs")
        for i, url in enumerate(settings.chat_worker_urls, 1):
            print(f"   {i}. {url}")
    else:
        print(" Chat Workers:  Không có URL nào được cấu hình")
    
    if settings.quiz_worker_urls:
        print(f" Quiz Workers: {len(settings.quiz_worker_urls)} URLs")
        for i, url in enumerate(settings.quiz_worker_urls, 1):
            print(f"   {i}. {url}")
    else:
        print(" Quiz Workers:  Không có URL nào được cấu hình")
    print("="*50 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,  
        log_level="info"
    )

def setup_ngrok():
    if not settings.ngrok_auth_token:
        print("  No NGROK_AUTH_TOKEN found in .env file")
        print("  Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken")
        return None
    
    try:
        ngrok.set_auth_token(settings.ngrok_auth_token)
        
        tunnel = ngrok.connect(settings.server_port, proto="http")
        public_url = tunnel.public_url
        
        print(f" Ngrok tunnel created!")
        print(f" Public URL: {public_url}")
        print(f" API Docs: {public_url}/docs")
        
        return public_url
    except Exception as e:
        print(f" Ngrok error: {e}")
        return None

if __name__ == "__main__":
    if not os.path.exists(".env"):
        print(" File .env not found!")
        print(" Create .env file from .env.example")
        sys.exit(1)
    
    if not os.path.exists(settings.rag_jsonl_path):
        print(f" RAG data file not found: {settings.rag_jsonl_path}")
        print("  Please place your rag.jsonl file in the data/ directory")
        sys.exit(1)
    
    use_ngrok = input("Do you want to expose server to public via ngrok? (y/n): ").lower().strip()
    
    if use_ngrok == 'y':
        public_url = setup_ngrok()
        if public_url:
            print(f"\n Copy this URL to your Frontend config:")
            print(f"   NEXT_PUBLIC_API_URL={public_url}")
    
    run_server()