# 환경아카이브 풀숲 임팩트 측정 보고서 — 분석 데이터

> 최신 보고서는 v1.1(2026-10-01, 62쪽)입니다. 아래 데이터와 그림 번호는 v1.0 작성 당시 기준이며 v1.1에서도 같은 데이터를 사용했습니다.

「환경아카이브 풀숲 · 환경사진아카이브 · 공간풀숲 임팩트 측정 보고서」(재단법인 숲과나눔, 2026.10.1 발행, v1.0) 작성에 사용한 데이터, 정제 표, 그림, 스크립트를 정리한 패키지입니다.
Omeka 소장기록 전수 분석(Ⅰ부 2장 「소장 기록의 구성」·「기록으로 본 환경운동 40년」, 그림 1~13·23·24)의 데이터는 이 저장소의 `data/holdings/*.json`(holdings·collections·keywords_* 등)을 그대로 사용했으므로 여기에 중복 수록하지 않았습니다.

## 폴더 구성

| 폴더 | 내용 |
|---|---|
| `raw/` | 재단이 제공한 원자료 엑셀 3종 (GA 통계 2종, 공간풀숲 전시 기록) |
| `processed/` | 원자료 시트별 CSV 내보내기 + 보고서에 수록한 정제 표 CSV |
| `figures/` | 보고서 수록 그림 PNG (그림 번호 = 보고서 v1.0 기준, `captions.json`에 캡션) |
| `scripts/` | 그림 생성·보고서 조판 스크립트 (Python) |

## raw/ — 원자료

| 파일 | 출처 | 기간 | 내용 |
|---|---|---|---|
| `pulsoop_ga_2025-06_2026-05.xlsx` | Google Analytics 4 (ecoarchive.org) | 2025.06.01~2026.05.31 | 사용자·페이지뷰·이벤트, 유입 경로, 구글 자연 검색어, 인기 페이지, 내부 검색어, 성별·연령·기기·국가별 사용자 |
| `epa_ga_2021-07_2026-06.xlsx` | Google Analytics 4 (환경사진아카이브) | 2021.07.01~2026.06.30 (5개 운영연도) | 연도별 사용자·페이지뷰·이벤트, 유입 경로, 인기 페이지, 기기·국가별 사용자. ※ 구글 검색어·내부 검색어·성별연령은 미설정으로 데이터 없음 |
| `gongan_pulsoop_exhibitions_2025-07_2026-08.xlsx` | 재단 전시 기록 정성·정량 평가 | 2025.07~2026.08 | 전시 목록·상세, 정량 성과, 정성자료(관람객 후기·언론 평가·작가 후기), 임팩트 기록, 기사 링크 (사진 제외) |

풀숲의 2020-21~2024-25 운영연도 수치는 v0.1 보고서(2026.5)에 수록된 이전 GA 집계를 그대로 사용했으며, 원자료 파일은 이 패키지에 없습니다(`processed/pulsoop_yearly_2020-2026.csv`에 수치만 수록).

**이용 시 유의**: `gongan_pulsoop_exhibitions_*.xlsx`의 「정성자료」 시트와 `processed/gongan_exhibitions__정성자료.csv`에는 방명록·SNS 댓글 등 관람객이 남긴 문장이 있습니다. 재단의 검토를 거쳐 공개하며, 인용 시 작성자를 특정하지 않도록 유의하시기 바랍니다.

## processed/ — 정제 표 (보고서 수록 수치)

| 파일 | 보고서 위치 | 내용 |
|---|---|---|
| `pulsoop_yearly_2020-2026.csv` | Ⅱ부 2·3장 | 풀숲 운영연도별 사용자·페이지뷰·이벤트 (6년 누적 270,310 / 733,321 / 1,255,014) |
| `pulsoop_events_2023-2026.csv` | Ⅱ부 4장 | GA4 이벤트 유형별 3년 |
| `pulsoop_channels_2023-2026.csv` | Ⅱ부 5장 | 신규 사용자 유입 채널 3년 |
| `pulsoop_age_2023-2026.csv` | Ⅱ부 7장 | 연령대 구성비 3년 |
| `omeka_summary_2026-08.csv` | Ⅰ부 2장 | 2026.8 Omeka REST API 재산출 (아이템·컬렉션·유형·전시) |
| `epa_yearly_2021-2026.csv` | Ⅲ부 3장 | 환경사진아카이브 5개 운영연도 |
| `epa_channels_2021-2026.csv` | Ⅲ부 4장 | 유입 채널 5년 |
| `epa_archiving_yearly_2021-2025.csv` | Ⅲ부 1장 | 연도별 아카이빙 작가·사진 건수 (누적 95인·21,248건) |
| `epa_webzine_issues_2021-2025.csv` | 부록 B | 웹진 EPAZINE 1~66호 (43~66호는 웹사이트 목록 캡처 기준) |
| `epa_sns_posts_2022.csv` | 부록 C | 2022년 SNS 게시물 41건 도달 수 |
| `epa_press_2021-07.csv` | 부록 D | 오픈 언론 보도 14건 |
| `epa_artists_2021.csv`, `epa_artists_2022-2023.csv` | 부록 A | 참여 작가 명단 |
| `gongan_summary_2025-07_2026-08.csv` | Ⅳ부 2장 | 공간풀숲 정량 성과 요약 |
| `gongan_exhibitions_visitors.csv` | Ⅳ부 2장 그림 | 관람객 집계 8개 전시의 관람객·보도 건수 |

원자료 시트 CSV (파일명 = `원자료__시트명.csv`):

| 파일 | 내용 |
|---|---|
| processed/pulsoop_ga_2025-26__개요.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__03_이벤트_수.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__04_유입_경로.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__05_구글_자연_검색어.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__06_인기_페이지.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__07_내부_검색어.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__08_성별_이용자.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__09_연령별_이용자.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__10_기기별_이용자.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/pulsoop_ga_2025-26__11_국가별_이용자.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/epa_ga_5yr__개요.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/epa_ga_5yr__03_이벤트_수.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/epa_ga_5yr__04_유입_경로.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/epa_ga_5yr__06_인기_페이지.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/epa_ga_5yr__10_기기별_이용자.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/epa_ga_5yr__11_국가별_이용자.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/gongan_exhibitions__전시_목록.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/gongan_exhibitions__전시_상세.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/gongan_exhibitions__정량성과.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/gongan_exhibitions__정성자료.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/gongan_exhibitions__임팩트_기록.csv | 원자료 시트 그대로 내보낸 CSV |
| processed/gongan_exhibitions__기사링크.csv | 원자료 시트 그대로 내보낸 CSV |

## figures/ — 보고서 그림

번호는 보고서 v1.0 기준입니다. 그림 1~13·23·24는 `data/holdings/*.json`으로, 14~22는 `processed/`의 표로 생성했습니다.

| 파일 | 캡션 |
|---|---|
| fig01.png | 컬렉션별 등록·공개 기록 수 (등록 30건 이상) |
| fig02.png | 컬렉션별 기록유형 구성비 |
| fig03.png | 컬렉션별 생산연대 분포 |
| fig04.png | 컬렉션별 주제 분포 |
| fig05.png | 컬렉션별 지역 분포 (키워드·태그 기준 추정, 지역 식별 60건 이상 컬렉션) |
| fig06.png | 소장 기록의 지역 분포 (키워드·태그 기준 추정) |
| fig07.png | 소장 기록의 생산연도 분포 (1980~2025, 생산연도 기재 공개 기록) |
| fig08.png | 연대별 주제 구성비 (주제 부여 기록 48,400건) |
| fig09.png | 연대별 상위 키워드 (출현 건수 상위 10개) |
| fig10.png | 연대별 특징 키워드 (전체 대비 출현 비율 상위 8개) |
| fig11.png | 5년 단위 상위 키워드 순위 변화 (1980~2024, 상위 10위) |
| fig12.png | 키워드의 생애 — 등장·정점·퇴장 (출현 건수 상위 40개) |
| fig13.png | 연대 사이의 급상승·급락 키워드 (점유율 변화 상위·하위 8개) |
| fig14.png | 운영연도별 연간 사용자 수 추이 (2020-21 ~ 2025-26) |
| fig15.png | 운영연도별 이벤트 유형별 발생 건수 (2023-2026) |
| fig16.png | 운영연도별 신규 사용자 유입 채널 구성비 |
| fig17.png | 2025-26년 Google 자연 검색 클릭수 상위 키워드 |
| fig18.png | 2024-25년 사이트 내부 검색어 상위 키워드 |
| fig19.png | 운영연도별 연령대 구성비 |
| fig20.png | 환경사진아카이브 연도별 아카이빙 사진 건수와 신규 참여 작가 수 (2021~2025) |
| fig21.png | 환경사진아카이브 운영연도별 사용자 수·페이지 조회수 (2021-22 ~ 2025-26) |
| fig22.png | 전시별 관람객 수 및 언론 보도 건수 (관람객 집계 시작 이후 8개 전시) |
| fig23.png | 월별 아이템 등록 건수 (2020.5 ~ 2026.9, 4천 건 이상 월 표시) |
| fig24.png | 단체 컬렉션 × 공통 키워드 출현 비율 |

## scripts/

| 파일 | 역할 |
|---|---|
| `make_figs.py` | `data/holdings/*.json` → 그림 1~13·23·24 (Omeka 전수 분석). 경로 상수 `D`·`OUT`과 글꼴 경로를 환경에 맞게 수정해 실행 |
| `v4lib.py` | 보고서 서식(v0.1 스타일) XML 생성 헬퍼 (python-docx) |
| `build_v04.py`, `build_v05.py`, `build_v10.py` | 보고서 docx 단계별 조판 스크립트 (v0.3 → v0.4 → v0.5~0.9 → v1.0). 경로가 작업 환경(`/home/claude`) 기준이므로 재실행 시 수정 필요 |

그래프 팔레트: `#2E6E3F` `#4C9A5A` `#8FCB94` (초록 계열), 글꼴 Noto Sans CJK KR.

## 데이터 출처 및 이용

- Google Analytics 데이터: 재단법인 숲과나눔 (ecoarchive.org, ecophotoarchive.org 속성)
- Omeka 소장기록: 환경아카이브 풀숲 REST API (2026.8 요약 / 2026.9.10 전수)
- 전시 기록: 재단법인 숲과나눔 공간풀숲
- 웹진 목록: ecophotoarchive.org/webzine (2026.9 확인)

보고서 작성: 이지현(재단법인 숲과나눔) · 최연하(에코아카이브아트센터) · 안대진(아카이브랩). 데이터 집계·그림 생성·문서 조판에 생성형 AI(Anthropic Claude)를 활용하였습니다.
