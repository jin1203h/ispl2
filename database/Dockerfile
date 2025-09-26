# ISPL PostgreSQL + pgvector 데이터베이스 컨테이너
# shrimp-rules.md 규칙: pgvector/pgvector:pg17 이미지 필수 사용

FROM pgvector/pgvector:pg17

# 환경 변수 설정
ENV POSTGRES_DB=ispldb
ENV POSTGRES_USER=admin
ENV POSTGRES_HOST_AUTH_METHOD=trust

# 초기화 스크립트 복사
COPY init.sql /docker-entrypoint-initdb.d/

# 데이터 디렉토리 생성
RUN mkdir -p /var/lib/postgresql/data

# 포트 5432 노출 (shrimp-rules.md 규칙 준수)
EXPOSE 5432

# PostgreSQL 시작
CMD ["postgres"]


