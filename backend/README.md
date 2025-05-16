# Better Blog Backend

더 나은 블로그 플랫폼을 위한 백엔드 서비스입니다.

## 기술 스택

- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Docker

## 개발 환경 설정

1. 의존성 설치:
```bash
poetry install
```

2. 환경 변수 설정:
```bash
cp .env.example .env
```

3. 개발 서버 실행:
```bash
docker-compose up --build
```

## API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 
