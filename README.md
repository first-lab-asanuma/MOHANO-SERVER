# MOHANO-SERVER

MOHANO 앱의 인증, 프로필, 매칭, 채팅, P2P 음성 통화 signaling을 위한 FastAPI 서버다.
음성 미디어는 WebRTC P2P로 앱 간에 직접 전달하며, 이 서버는 오디오를 중계하지 않는다.

## 현재 범위

- `GET /v1/health`
- 익명 사용자 생성과 access/refresh JWT 발급·갱신·로그아웃
- 프로필 텍스트·사진 참조값은 MySQL에 저장되며, 사진 원본은 private S3 호환 object storage에 둔다.
- 매칭 조건·후보, 통화 신청·P2P signaling, REST 채팅·읽음 API
- 매칭·통화·채팅 데이터는 개발용 `MockStore`에만 저장된다. FastAPI를 재시작하면 사라진다.

LINE·Apple credential 검증과 매칭·통화·채팅 MySQL repository는 기능별 설계 문서에 따라
다음 단계에서 구현한다.

## 실행 준비

### 로컬 인프라 컨테이너

`etc/infra`에는 로컬 전용 MySQL과 Silo(MinIO 호환)가 함께 준비된다. 별도 infra `.env` 파일 없이
`etc/infra`에서 다음을 실행한다.

    docker compose up -d --build

MySQL은 기본적으로 `127.0.0.1:3306`에만 열리며, FastAPI는 로컬 Python 프로세스로
실행한다. Silo S3 API는 `http://127.0.0.1:9000`, 관리 콘솔은
`http://127.0.0.1:9001`에만 열린다. Compose 기동 뒤 `minio-init` 작업이 성공 종료하면
비공개 `mohano-profile-images` 버킷을 사용할 수 있다.

Silo는 MinIO 호환 로컬 사진 저장소다. FastAPI는 짧게 만료되는 signed PUT/GET URL만 발급하고,
앱은 장기 storage 자격 증명 없이 사진을 직접 업로드·조회한다. 운영에서는 같은 S3 호환 계약을
Cloudflare R2로 전환한다.

### FastAPI

사용 중인 Python으로 가상 환경을 만들고 의존성을 설치한다. 더미 API 단계에서는 MySQL을
실행하거나 migration을 적용할 필요가 없다. `.env.example`을 `.env`로 복사해 최소한
`MOHANO_JWT_SECRET_KEY`를 안전한 값으로 변경한다.

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -e ".[dev]"
    uvicorn app.main:app --reload

MySQL 전환 시에만 `alembic upgrade head`를 실행한다. 서버 실행과 migration은 사용자가
수행한다. 실제 OAuth provider secret과 JWT secret은 저장소에 추가하지 않는다.

### Flutter Web 로컬 연동

기본 CORS 설정은 `localhost`와 `127.0.0.1`의 로컬 포트만 허용한다. Flutter 앱은 별도 설정이
없으면 `http://127.0.0.1:8000/v1`을 사용한다. 다른 개발 서버 주소를 쓸 때만 Flutter 실행에
`--dart-define=MOHANO_API_BASE_URL=http://<host>:<port>/v1`을 추가한다.

### VS Code F5 실행

Python 확장을 설치한 뒤 `MOHANO-SERVER` 폴더를 VS Code 작업 폴더로 열고 F5를 누른다.
`.vscode/launch.json`의 `MOHANO Server (FastAPI)` 설정은 아래 명령과 같은 서버를 debug
mode로 기동한다.

    python -m uvicorn app.main:app --reload

## 설계 문서

서버 설계의 기준은 `etc/design/00-start.txt`와 기능별 문서다.
