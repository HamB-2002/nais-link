# 출처 (SOURCE.md)

- 자료명: 「환경아카이브 풀숲 · 환경사진아카이브 · 공간풀숲 임팩트 측정 보고서」 v1.1 (2026년 10월 1일 발행)
- 발행 기관: 재단법인 숲과나눔 (원본 저장소 소유: ArchivelabEdu)
- 원본 URL: <https://github.com/ArchivelabEdu/ecoarchive-impact2026> — 커밋 `61265f886371c4c5810cf2fb300fa5cc7b4d3f3a`
- 라이선스: MIT License — 원본 저장소의 `LICENSE` (이 폴더의 `LICENSE`)
- 받은 날짜: 2026-10-01
- 구성:
  - 보고서: `report.docx` ← 원본 `report/pulsoop-impact-report-2026-v1.1.docx` (한국어, 표 58개, **그림 제거본**)
  - 코드: `code/` ← 원본 `data/impact/scripts/` (파이썬 5개)
  - 데이터: `data/raw/` ← 원본 `data/impact/raw/` 중 Google Analytics 통계 엑셀 2개, `data/processed/` ← 원본 `data/impact/processed/` 중 CSV 36개
  - 원본 안내문: `ORIGINAL_README.md` ← 원본 `data/impact/README.md` (정제 표가 보고서의 어느 장 수치인지 대응표가 있음)
- 개인정보 포함 여부: 없음 — 이메일·전화번호 패턴이 없음을 확인함. 다만 보고서와 `data/processed/epa_artists_*.csv`에 사업 참여 작가의 성명이 있으며, 원 보고서 부록에 실린 공개 정보이다. 방문객 후기 문장이 든 자료는 뺐다.
- 원본 그대로 여부: 아니오 — 보고서에서 그림을 제거하고 일부 파일을 뺐다.

## 원본에서 바꾼 것·뺀 것
- **보고서 그림 제거**: `report.docx`는 원본 docx(3,356KB)에서 삽입된 그림 40개를 모두 지운 것이다(107KB). 이유: 보고서에 사진작가의 작품 사진, 전시장 사진, 웹사이트 화면이 들어 있어 저장소의 MIT 라이선스가 제3자 저작물까지 포함하는지 확실하지 않기 때문이다. 도구는 python-docx이다.
  - 검증(2026-10-01): 문단 440개, 표 58개, 공백을 뺀 글자 44,191자, 숫자 표기 2,074개가 원본과 모두 같다. 그림 캡션 문구(「[그림 N …]」)는 남아 있고, 끊어진 그림 참조는 없다.
- **뺀 파일**: 보고서 PDF 2종(그림 포함), `figures/`(보고서 그림 PNG), `data/impact/raw/gongan_pulsoop_exhibitions_2025-07_2026-08.xlsx`와 `data/impact/processed/gongan_exhibitions__정성자료.csv`(관람객·작가 후기 문장이 들어 있어 원 안내문이 이용 시 유의를 안내함), `data/holdings/`(사이트용 집계 JSON), 사이트 템플릿 등 나머지 저장소 파일.
- 코드·데이터·`LICENSE`는 원본 커밋에서 받아 Git 해시가 모두 일치함을 확인한 뒤 그대로 두었다.

## 알아둘 점
- `code/`의 스크립트는 **보고서 조판과 그림 생성용**이다. 집계값을 계산하는 코드가 아니며, 표의 수치가 코드에 직접 적혀 있고, 입력·출력 경로가 저자 작업 환경(`/home/claude/...`)이라 이 폴더에서 재실행되지 않는다.
- 그래서 이 자료로 시험할 수 있는 것은 「보고서 수치 → 정제 표 CSV → 원자료 엑셀」로 이어지는 연결이다. 정제 표를 원자료에서 계산한 코드는 없으므로, 「수치를 만든 코드 줄 찾기」에는 맞지 않고 「출처 미확인」이 나오는 것이 정상이다.
- 확인한 대응 예(보고서 본문에도 같은 값이 있음): 풀숲 6년 누적 사용자 270,310 · 페이지뷰 733,321 · 이벤트 1,255,014(`data/processed/pulsoop_yearly_2020-2026.csv`), Omeka 등록 아이템 111,106(`data/processed/omeka_summary_2026-08.csv`), 환경사진아카이브 누적 작가 95인 · 사진 21,248건(`data/processed/epa_archiving_yearly_2021-2025.csv`).
- `ORIGINAL_README.md`가 언급하는 `figures/` 등 일부 파일은 이 폴더에 없다.
