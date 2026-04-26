# 🚀 설정 및 실행 가이드

### Docker Compose 실행

Docker Compose로 백엔드, 프론트엔드, Redis를 함께 실행합니다.

1) 실행

```bash
git submodule update --init --remote
docker compose up --build
```

프론트엔드는 Nginx로 정적 빌드 결과물을 서빙합니다. Compose는 프론트엔드 빌드 인자 `API_BASE_URL`로 `http://localhost:44345`를 전달합니다.

2) 접속

- 프론트엔드: http://localhost
- API: http://localhost:44345
- 백엔드 컨테이너 내부 통신: http://backend:8000
