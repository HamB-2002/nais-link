# 출처 (SOURCE.md)

- 자료명: *Outcome Without Method: An Outcome-Validation Integrity Score for Agentic Cybersecurity Benchmarks*
- 발행 기관: Babar Khan Akhunzada (SecurityWall)
- 원본 URL: <https://zenodo.org/records/22016351> (DOI 10.5281/zenodo.22016351), 공개일 2026-08-19
- 라이선스: CC BY 4.0 — <https://creativecommons.org/licenses/by/4.0/> (출처 표시 필수)
- 받은 날짜: 2026-10-01
- 구성 (원본 레코드의 파일 이름과 폴더를 그대로 둠 — 스크립트가 같은 폴더의 CSV를 읽기 때문):
  - 보고서: `OVIS_paper.pdf`(영어, 7쪽), `OVIS_paper_source.tex`(LaTeX 원본)
  - 코드: `01_ovis_scoring_and_group_means.py`, `02_significance_tests.py`, `03_make_figures.py` (파이썬)
  - 데이터: `master_dataset.csv`
  - 저장된 결과: `ovis_scored_table.csv`, `ovis_summary_stats.json`, `Fig1_ovis_ranked.*`, `Fig2_jwt_case.*`
- 개인정보 포함 여부: 없음. 논문 첫 쪽에 저자가 공개한 연락용 이메일 주소가 있다.
- 원본 그대로 여부: 예 — 12개 파일 모두 Zenodo에 등록된 md5 체크섬과 일치한다.

## 알아둘 점
- 재실행 결과(2026-10-01, Python 3.14.4, pandas 3.0.6, scipy 1.18.1): `python 01_ovis_scoring_and_group_means.py`와 `python 02_significance_tests.py`가 오류 없이 실행되고, 새로 만든 `ovis_scored_table.csv`와 `ovis_summary_stats.json`이 저장된 원본과 **완전히 같았다.** `03_make_figures.py`는 실행하지 않았다.
- 논문 본문의 표·문장에 있는 값(전체 평균 OVIS 60.0%, σ = 20.0, 결과 중심 설계 50.0%, 과정 인식 설계 67.5%, 방법 검증 평균 16.7%/100.0%)은 코드 출력과 일치한다.
- **코드 출력과 논문이 다른 곳**: `02_significance_tests.py`는 「논문 한계 절에 인용된 값」이라며 `U = 0, p = 0.009`(Mann-Whitney)와 `p = 0.076`(Fisher)를 출력하지만, 이 논문 PDF와 LaTeX 원본에는 그 값도, Mann-Whitney·Fisher라는 말도 없다(2026-10-01 검색). 논문이 고쳐지면서 빠진 것으로 보인다.
- **실행하면 같은 이름의 결과 파일이 덮어써진다**(내용은 같음). 이 폴더를 복사한 뒤 실행할 것.
