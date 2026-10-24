# MOHANO-SERVER 에이전트 작업 규칙

이 파일은 `MOHANO-SERVER`를 수정하는 에이전트가 따라야 할 규칙이다. 제품 흐름과
Flutter 화면은 `MOHANO-APP/etc/design/`을 참고하되, 서버의 설계 기준은 이 저장소의
`etc/design/`을 단일 기준으로 삼는다.

## 작업 범위

1. 에이전트는 서버 코드, 설정, 문서, 마이그레이션, 테스트 코드만 수정한다.
2. 실행, 패키지 설치, DB 생성·변경, migration 실행, 테스트, Git 명령은 사용자가 수행한다.
3. 외부 OAuth 제공자, STUN/TURN, 배포, 비밀 키, 운영 DB에 연결하거나 상태를 바꾸지 않는다.
4. 로컬 파일 수정에는 `apply_patch`를 사용한다.

## 서버 기술 기준

1. 서버는 Python FastAPI 애플리케이션으로 만든다. API는 `/v1` 아래에 둔다.
2. 영속 데이터의 기준 저장소는 MySQL이다. 스키마 변경은 migration으로 관리한다.
3. API는 기능별 router, service, repository, schema 계층으로 나눈다. router에 DB 쿼리나
   OAuth 검증 로직을 직접 넣지 않는다.
4. router(Controller)는 HTTP 요청·응답과 인증 의존성만 처리하고, 각 기능의 비즈니스 규칙은
   `app/services/`의 기능별 클래스에 둔다. 임시 더미 데이터도 router가 아닌 service를 통해서만
   읽고 변경한다.
5. 인증은 LINE, Google, Apple credential을 서버에서 검증한 뒤 발급하는 access JWT와
   refresh JWT를 사용한다. refresh JWT 원문을 DB에 저장하지 않고 `jti` 해시와 폐기 상태만
   저장한다.
6. 비밀 값과 provider secret은 소스·문서·클라이언트에 넣지 않는다. 환경 변수 이름만
   문서화한다.

## 통신 및 실시간 규칙

1. 기본 통신은 HTTPS REST JSON이다. 채팅은 WebSocket을 사용하지 않으며, 앱 화면 진입과
   사용자의 새로고침 때 REST API로 조회한다.
2. 음성은 WebRTC P2P로 두 이용자가 직접 전송한다. 서버는 오디오를 수신·저장·중계하지
   않는다.
3. 서버는 인증된 두 참여자의 call request와 짧게 만료되는 SDP·ICE 신호만 REST polling으로
   전달한다. 신호 payload와 call session은 허가된 참여자만 읽거나 쓸 수 있어야 한다.
4. P2P 직결 실패에 대한 TURN relay 도입은 별도 사용자 결정 전에는 구현하지 않는다.

## API 및 보안 규칙

1. 요청과 응답은 Pydantic schema로 명시한다. 성공·실패 응답, 권한 오류, pagination/cursor를
   일관된 형식으로 유지한다.
2. 모든 사용자 데이터 API는 현재 사용자 인증과 리소스 소유권 검사를 거친다.
3. 후보 ID, chat ID, call session ID는 유추 가능한 순번을 외부 계약으로 사용하지 않는다.
4. 서버 로그에 OAuth credential, JWT, SDP/ICE 전체 payload, 개인정보를 기록하지 않는다.
5. 기능이 목업이거나 API만 정의된 상태라면 실제 동작 완료처럼 표현하지 않는다.

## 설계 기록 의무

1. 작업 전 `etc/design/00-start.txt`와 관련 기능 문서를 읽는다.
2. 기능 하나당 하나의 `.txt` 파일만 사용하고, 날짜별 파일을 만들지 않는다.
3. 문서에는 변경 목적, 확정한 결정, API/데이터 요구사항, 영향 파일, 다음 작업 또는
   미결정 사항을 남긴다.
4. 서버 설계의 단일 기준은 이 저장소의 `etc/design`이다. Flutter 쪽에는 클라이언트
   연동 사항만 남긴다.

## 완료 보고 규칙

1. 결과와 수정 파일을 절대 경로 링크로 짧게 보고한다.
2. 실행·DB migration·테스트를 하지 않았으면 이를 명시하고 사용자가 확인할 항목만 안내한다.
