# 출처 (SOURCE.md)

`sample-10`의 보고서를 docx에서 hwpx로 **형식만 변환**한 자료이다. 코드와 데이터는 `sample-10`과 같다.

- 자료명: 「미술현장의 정보격차 해소를 위한 생성형 AI 기반 '광역 리서치' 실행연구」 보충자료 — 자기일치도(교차모델) 재코딩 검증 보고서 (hwpx 변환본)
- 발행 기관: Kim, Kyu hyung (Chonnam National University)
- 원본 URL: <https://zenodo.org/records/22157092> (DOI 10.5281/zenodo.22157092)
- 라이선스: CC BY 4.0 — <https://creativecommons.org/licenses/by/4.0/> (출처 표시 필수, 변경 사실 표시)
- 받은 날짜: 2026-09-30
- 구성: `report.hwpx`(변환본), `code/`, `data/` — `code/`와 `data/`는 `sample-10`과 동일
- 개인정보 포함 여부: 없음
- 원본 그대로 여부: 아니오 — 보고서를 docx에서 hwpx로 변환함

## 원본에서 바꾼 것
- 변경한 파일: `reliability_crossmodel_report.docx` → `report.hwpx`
- 무엇을 어떻게 바꿨는지: 도구 `pypandoc-hwpx` 0.1.1(MIT, Pandoc 3.9 사용)로 파일 형식만 변환함. 문서 내용은 바꾸지 않음. 글꼴, 여백, 문단 스타일은 도구의 기본 서식으로 바뀜.
- 바꾼 이유: 한글(hwpx) 문서에서 수치·표를 추출하는 기능을 시험하기 위함. 원본 저자가 만든 hwpx가 아니라 자동 변환본이다.
- 변환 결과 검증(2026-09-30): 표 8개의 행·열 수 일치, 공백을 뺀 글자 수 15,793자 일치, 숫자 표기 512개가 빠지거나 늘지 않고 일치. `python-hwpx`로 정상적으로 열림을 확인함.
- 한컴 한글 프로그램에서의 열림 확인: 아직 하지 않음
