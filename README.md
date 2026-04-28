# 🚀 설정 및 실행 가이드

### Docker Compose 실행

Docker Compose로 백엔드, 프론트엔드, Redis를 함께 실행합니다.

### 1) 실행

백엔드, 프론트엔드의 개발 레포지토리로 부터 최신 버전 소스코드를 불러옵니다.

```bash
git submodule update --init --remote
```

도커 이미지를 빌드하고 서비스를 구성하여 배포합니다.
```
docker compose up --build
```

### 2) 접속

- 프론트엔드: http://localhost:8000
- API: http://localhost:8080

### 3) 준비

- 게임을 생성해야 합니다. `http://localhost:8080/docs`(백엔드 서버) 에 접속하여 `/api/v1/games`(게임 생성 API) 를 호출하여 게임을 설정합니다. (게임 준비에 약 20~30초 소요됩니다.)
