from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

from src.api.dependencies.settings import get_settings
from src.api.routes import auth, category, comment, post

settings = get_settings()

description = """
Better Blog API는 현대적이고 확장 가능한 블로그 플랫폼을 위한 RESTful API입니다.

## 주요 기능

### 인증
* 회원가입 및 로그인
* JWT 기반 인증
* 역할 기반 접근 제어

### 블로그 포스트
* 포스트 CRUD
* 카테고리 관리
* 태그 지원
* 조회수 및 좋아요

### 댓글
* 계층형 댓글 (대댓글)
* 좋아요
* 작성자 권한 관리

### 카테고리
* 계층형 카테고리 구조
* 카테고리별 통계
* 순서 관리

### 통계
* 포스트별 통계
* 카테고리별 통계
* 댓글 통계
* 사용자 활동 통계
"""

app = FastAPI(
    title=settings.APP_NAME,
    description=description,
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "개발팀",
        "url": "http://example.com/contact/",
        "email": "dev@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    debug=settings.DEBUG,
    docs_url=None,
    redoc_url=None,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(post.router, prefix=settings.API_V1_PREFIX)
app.include_router(category.router, prefix=settings.API_V1_PREFIX)
app.include_router(comment.router, prefix=settings.API_V1_PREFIX)

# 커스텀 OpenAPI 스키마
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=[
            {
                "name": "auth",
                "description": "사용자 인증 및 권한 관리",
            },
            {
                "name": "posts",
                "description": "블로그 포스트 관리",
            },
            {
                "name": "categories",
                "description": "카테고리 관리",
            },
            {
                "name": "comments",
                "description": "댓글 관리",
            },
        ],
    )
    
    # 보안 스키마 추가
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT 토큰을 입력하세요. 예: 'Bearer your-token-here'",
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 커스텀 문서 엔드포인트
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )

@app.get("/")
async def root():
    """Better Blog API에 오신 것을 환영합니다."""
    return {
        "message": "Welcome to Better Blog API",
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
        }
    } 
 