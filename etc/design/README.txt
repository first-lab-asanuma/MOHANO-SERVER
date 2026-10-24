MOHANO-SERVER design work log
=============================

Purpose
-------
이 폴더는 MOHANO 서버의 API, 데이터, 보안, P2P signaling 설계의 단일 기준이다.
Flutter 화면과 클라이언트 연동 메모는 `MOHANO-APP/etc/design`에 둔다.

Rules
-----
- 기능 하나당 하나의 `.txt` 파일만 사용한다.
- `00-start.txt`를 먼저 읽고, 이후 관련 기능 문서를 갱신한다.
- 각 문서에는 변경 목적, 확정한 결정, API/데이터 요구사항, 영향 파일, 다음 작업 또는
  미결정 사항을 기록한다.
- 날짜별 회의록이나 생성 자산은 이 폴더에 두지 않는다.
