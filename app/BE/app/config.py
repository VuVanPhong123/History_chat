from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pydantic import Field, validator, model_validator
import os
import json

class Settings(BaseSettings):
    
    environment: str = Field(
        default="development",
        description="Môi trường: development, staging, production"
    )
    
    server_host: str = Field(
        default="0.0.0.0",
        description="Host để bind server"
    )
    
    server_port: int = Field(
        default=8000,
        description="Port để chạy server"
    )
    
    database_url: str = Field(
        default="sqlite:///./history.db",
        description="Connection string cho database"
    )
    
    secret_key: str = Field(
        ... ,  
        description="Secret key để ký JWT token - BẮT BUỘC"
    )
    
    algorithm: str = Field(
        default="HS256",
        description="Thuật toán mã hóa JWT"
    )
    
    access_token_expire_minutes: int = Field(
        default=5,
        description="Thời gian hết hạn token (phút)"
    )
    
    admin_password: str = Field(
        ... ,  
        description="Mật khẩu admin - BẮT BUỘC"
    )
    
    rag_jsonl_path: str = Field(
        default="./data/rag.jsonl",
        description="Đường dẫn đến file RAG JSONL"
    )
    
    ngrok_auth_token: Optional[str] = Field(
        default=None,
        description="Token ngrok"
    )
    
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="URL của frontend để cấu hình CORS"
    )
    
    # Thay đổi: Sử dụng string thay vì List[str]
    chat_worker_urls_str: str = Field(
        default="",
        description="Danh sách chat worker URLs (phân cách bằng dấu phẩy)"
    )
    
    quiz_worker_urls_str: str = Field(
        default="",
        description="Danh sách quiz worker URLs (phân cách bằng dấu phẩy)"
    )
    
    @model_validator(mode='after')
    def validate_settings(self):
        """Kiểm tra các biến bắt buộc"""
        errors = []
        
        if not self.secret_key or self.secret_key.startswith("your-"):
            errors.append("SECRET_KEY phải được đặt trong .env và không được dùng giá trị mặc định")
        
        if not self.admin_password or self.admin_password == "admin123":
            errors.append("ADMIN_PASSWORD phải được đặt trong .env và không được dùng mật khẩu mặc định")
        
        if not os.path.exists(self.rag_jsonl_path):
            errors.append(f"File RAG không tồn tại: {self.rag_jsonl_path}")
        
        if errors:
            raise ValueError("\n".join(errors))
        
        return self
    
    # Thêm property để lấy danh sách URLs đã parse
    @property
    def chat_worker_urls(self) -> List[str]:
        return self._parse_urls(self.chat_worker_urls_str)
    
    @property
    def quiz_worker_urls(self) -> List[str]:
        return self._parse_urls(self.quiz_worker_urls_str)
    
    def _parse_urls(self, urls_str: str) -> List[str]:
        """Parse string URLs thành list"""
        if not urls_str or not urls_str.strip():
            return []
        
        # Loại bỏ khoảng trắng và phân tách bằng dấu phẩy
        urls = [url.strip() for url in urls_str.split(',') if url.strip()]
        # Loại bỏ URL trùng lặp
        return list(dict.fromkeys(urls))
    
    @property
    def cors_origins(self) -> List[str]:
        origins = [
            "http://localhost:3000", 
            "http://127.0.0.1:3000",  
            "http://localhost:8000",  
        ]
        
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
            
        return list(set(origins))  
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  
    )

try:
    settings = Settings()
    print(f" Config loaded successfully")
    print(f"   Environment: {settings.environment}")
    print(f"   Server: http://{settings.server_host}:{settings.server_port}")
    print(f"   Chat Workers: {len(settings.chat_worker_urls)} URLs")
    if settings.chat_worker_urls:
        for url in settings.chat_worker_urls:
            print(f"     - {url}")
    print(f"   Quiz Workers: {len(settings.quiz_worker_urls)} URLs")
    if settings.quiz_worker_urls:
        for url in settings.quiz_worker_urls:
            print(f"     - {url}")
except Exception as e:
    print(f" Config validation failed: {e}")
    print(" Please check your .env file")
    raise