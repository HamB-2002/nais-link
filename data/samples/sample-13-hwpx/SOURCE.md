# 출처 (SOURCE.md)

`sample-13`의 논문을 LaTeX 원본에서 **hwpx로 변환한 자료**이다. 코드와 데이터는 `sample-13`과 같다.

- 자료명: *Outcome Without Method: An Outcome-Validation Integrity Score for Agentic Cybersecurity Benchmarks* (hwpx 변환본)
- 발행 기관: Babar Khan Akhunzada (SecurityWall)
- 원본 URL: <https://zenodo.org/records/22016351> (DOI 10.5281/zenodo.22016351), 공개일 2026-08-19
- 라이선스: CC BY 4.0 — <https://creativecommons.org/licenses/by/4.0/> (출처 표시 필수, 변경 사실 표시)
- 받은 날짜: 2026-10-01
- 구성 (`sample-13`과 같은 평면 구조 — 스크립트가 같은 폴더의 CSV를 읽기 때문):
  - 보고서: `report.hwpx` (변환본, 영어)
  - 코드: `01_ovis_scoring_and_group_means.py`, `02_significance_tests.py`, `03_make_figures.py`
  - 데이터·저장된 결과: `master_dataset.csv`, `ovis_scored_table.csv`, `ovis_summary_stats.json` (`sample-13`에서 그대로 복사함)
- 개인정보 포함 여부: 없음. 문서 첫머리에 저자가 논문에 공개한 연락용 이메일 주소가 있다.
- 원본 그대로 여부: 아니오 — 논문을 LaTeX에서 hwpx로 변환했다.

## 원본에서 바꾼 것
- 변경한 파일: `OVIS_paper_source.tex` → `report.hwpx`. 논문의 내용(문장·표·수치)은 바꾸지 않았다. 도구는 `pypandoc-hwpx` 0.1.1(MIT), Pandoc 3.9이다.
- 변환 도구가 처리하지 못하는 LaTeX 요소는 컴파일된 PDF(`sample-13/OVIS_paper.pdf`)에 보이는 형태의 글자로 바꿔 넣었다.
  - 인용 `\cite{...}` → PDF와 같은 번호(예: 「[1, 8, 9]」). 참고문헌 33개는 `\bibitem` 순서로 번호를 매겼다.
  - 상호참조 `\ref{...}` → PDF와 같은 표기(「Section III」, 「Eq. 1」, 「Table 1」, 「Figure 2」).
  - 수식 23개 → 유니코드 글자(수식 서식은 없음), 식 (1)의 번호 표기.
  - 표·그림 캡션 → 「Table N:」「Figure N:」로 시작하는 문단. 알고리즘 상자(Algorithm 1)는 일반 문단.
  - 절 제목에 PDF와 같은 번호(「I.」, 「A.」)를 붙임. 제목·저자·초록은 원문에서 가져와 문서 맨 앞에 넣음(변환기가 읽지 못하는 위치에 있음).
  - 그림 2개는 원본 PDF 대신 같은 그림의 PNG(`Fig1_ovis_ranked.png`, `Fig2_jwt_case.png`)를 넣음.
  - 2단 편집은 단일 단으로, 글꼴·여백은 도구 기본값으로 바뀜.
- 바꾼 이유: 한글(hwpx) 문서에서 수치·표를 추출하고 코드와 대조하는 기능을 시험하기 위함. 원 저자가 만든 hwpx가 아니라 자동 변환본이다.
- 변환 결과 검증(2026-10-01):
  - 변환 전 원문 조각 250개가 모두 본문에 있고 글자 수(공백 제외)가 26,103자로 같다.
  - 표 2개(12×10, 4×4)의 행·열 수가 원문과 같고, 그림 2개가 들어 있다.
  - 본문의 인용 표기 81개가 컴파일된 PDF의 81개와 종류·횟수까지 같다. 논문의 핵심 수치(60.0%, σ = 20.0, 67.5, 16.7, 100.0, 90.0)와 「Table 1:」「Table 2:」「Figure 1:」~「Figure 3:」가 들어 있다.
  - PDF 텍스트에는 있지만 이 문서에는 없는 것: 그림 안의 글자(예: 그림 1의 「mean = 60.0%」). 그림이 이미지로 들어가기 때문이다.
  - `python-hwpx`로 정상적으로 열림을 확인함.
- 한컴 한글 프로그램에서의 열림 확인: 아직 하지 않음

## 알아둘 점
`sample-13`의 `SOURCE.md`와 같다. 스크립트는 `master_dataset.csv`를 읽지 않고, 점수가 `01_...py` 안에 직접 적혀 있다.
