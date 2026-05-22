# Phase R12 — DROID/BridgeData 검증

## 목표
FGLC를 실제 로봇 데이터로 전이 (DROID RLDS, BridgeData V2).
시뮬레이션 물리학을 넘어선 일반화 검증.

## 단계

1. DROID: RLDS 형식을 FGLC 학습 형식으로 변환 (고유감각 + action, regime_id 사용 불가)
2. BridgeData V2: 기관 분할을 OOD로 사용 (다른 연구소 = 분포 이동)
3. 평가: 사용 가능한 하위 집합에서 return/recovery (oracl regime 레이블 없음 → 제어 지표만)

## 시뮬레이션과의 핵심 차이점
- regime_id 없음 → 탐지 AUROC 또는 마스크 정밀도/재현율 지표 계산 불가
- 평가가 다음으로 제한됨: 예측 NLL, return, 성공률, 회복 시간
- OOD는 데이터 소스로 정의되어야 함 (DROID collectors, BridgeData 기관)

## Gate 기준
- [ ] DROID (≥500 궤적 하위 집합)에서 FGLC 학습 및 평가됨
- [ ] 기본 WM 대비 보류된 기관의 NLL 개선
- [ ] BridgeData V2 기관 OOD 분할에서 return 개선

## 위험 등록부
- R-4 (ROADMAP/19): DROID 데이터셋 접근에 신청 필요 (~100GB)
- R-5: 실제 로봇 노이즈가 correction 신호를 압도할 수 있음; ECE가 시뮬레이션보다 나쁠 수 있음
