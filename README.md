# STORE CONNECT Spatial

VMD가 매장 공간을 이해하고 진열을 판단하며 현장과 요청·완료 보고·재확인을 이어가는 웹 시제품입니다.

- 실제 해커톤 데모: https://store-connect-spatial.vercel.app (로그인 없이 이용)
- 공개 소스: https://github.com/suneside/store-connect-spatial-public
- Three.js / Blender / Node.js / Vercel / Supabase
- 실제 데모의 사진 기반 상품 생성: Higgsfield / Tripo H3.1

## 공개본과 실제 데모

브라우저 3D 탐색, 집기 선택, 재고 검증, 다중 매장 설정, 현장 협업 API와 DB 스키마를 공개합니다. 제공 비공개 사진·출제 데이터·그로부터 생성한 사진 기반 모델·외부 참고 사진·키·원본 Git 이력은 포함하지 않습니다. 이 저장소에는 직접 만든 합성 재고와 코드로 생성한 상품·공간을 넣어 별도 자료 없이 실행할 수 있습니다. 실제 데모와 시각 애셋은 다릅니다. 집 컴퓨터 원본과 기존 배포 연결은 보존합니다.

## 실행

Node.js 24에서 `node scripts/serve_cloud.mjs` 실행 후 http://127.0.0.1:5190 접속. 기본 탐색과 매장 등록·초안은 별도 API 키 없이 동작합니다. `npm test`로 입력 검증·업무 상태 전환·매장 구분 테스트를 실행합니다.

공유 저장을 구성하려면 본인 Supabase 프로젝트에 `supabase/migrations`를 적용하고 `.env.example`을 `.env.local`로 복사해 서버 환경변수를 설정합니다. `node --env-file=.env.local scripts/serve_cloud.mjs`로 실행합니다. `SPATIAL_PUBLIC_DEMO=true`는 모두가 시연 데이터를 수정하는 공개 공간을 의미합니다. 키는 Git에 올리지 않습니다. Vercel은 `dist`와 `api`를 배포합니다.

## 사용 흐름

1. 1인칭·3인칭·전체 공간 전환. WASD 이동, 드래그 시선, 미니맵 확인.
2. 집기 → 상품·재고·기록 → 변경안의 재고·집기 수용량 검토.
3. 확인 요청 초안 → 현장 연결 → 현장에 요청 → 완료 보고 → VMD 재확인.
4. 매장 전환·관리 → 새 매장 → 도면 이미지·mm 치수·원점·회전·집기·재고 → 저장·공유.

개인 설정은 IndexedDB, 초안은 localStorage, 공유한 설정·업무는 Supabase에 저장합니다. 서버에서는 매장별 범위와 revision 충돌을 검사합니다. RLS를 유지하며 service_role 키는 서버에서만 사용합니다.

현재 리브 외형·리깅, 개인별 권한, 자체 상품 카탈로그/GLB 업로드, 실측 스캔, AI 자동 판정은 미완성입니다. 실측 디지털 트윈이나 실제 매장 실시간 재고로 표현하지 않습니다.

## 애셋과 코드

`scripts/detail_apparel.py`, `detail_accessories.py`는 외부 사진 없이 생성하는 모델 코드입니다. `scripts/export_public_models.py`로 Blender 5.2에서 공개용 GLB를 다시 생성합니다. 나머지 Blender 파이프라인 스크립트는 실제 데모 제작 과정의 코드로 공개하며 입력 비공개 자료는 별도 필요합니다. Three.js 라이선스는 `dist/vendor/three/LICENSE`에 있습니다. 목재·바닥 재질의 원 출처는 Poly Haven CC0입니다.
