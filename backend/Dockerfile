FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry

# Poetry 설정 (가상환경 생성하지 않음)
RUN poetry config virtualenvs.create false

# 소스 코드 복사
COPY . .

# 의존성 설치 (--no-dev 대신 --only main 사용)
RUN poetry install --only main --no-interaction --no-ansi

# Python 경로 설정
ENV PYTHONPATH=/app

# 실행
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 
