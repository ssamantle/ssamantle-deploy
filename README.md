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

- 프론트엔드: http://localhost:8000
- API: http://localhost:8080

3) 준비

- 게임을 생성해야 합니다. `http://localhost:8080/docs`(백엔드 서버) 에 접속하여 `/api/v1/games`(게임 생성 API) 를 호출하여 게임을 설정합니다. (게임 준비에 약 20~30초 소요됩니다.)
