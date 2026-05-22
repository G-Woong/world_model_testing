# Phase R16 — 최종 보고서 및 재현성 패키지

## 목표
LaTeX 조립, 최종 그림, 제출을 위한 재현성 패키지.

## 산출물
1. docs/paper/의 LaTeX 소스 (R14에서 생성 예정)
2. 실험 출력에서 생성된 최종 그림 (PDF/SVG)
3. 재현성 패키지: config/ + seeds/ + data_hashes/ + model_checkpoints/
4. 코드 공개: src/fglc/ + scripts/fglc/ + tests/ (공개 저장소)

## 재현성 요구사항
- 모든 결과가 추적 가능: config 파일 + seed + 데이터셋 hash + 모델 체크포인트 SHA256
- `scripts/fglc/11_generate_reports.py`는 아티팩트 파일에서만 읽음 (수동 숫자 없음)
- 모든 그림은 스크립트로 생성됨 (수동 그리기 도구 아님)

## Gate 기준
- [ ] LaTeX가 오류 없이 컴파일됨
- [ ] 모든 그림이 실행 아티팩트로 추적 가능함
- [ ] 재현성 패키지 ZIP 생성됨
- [ ] 최종 NLL/return/AUROC 숫자가 저장된 아티팩트와 대조 검증됨
- [ ] 보충 자료 부록이 제출 PDF에 포함됨
