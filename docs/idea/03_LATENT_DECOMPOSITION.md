# 03_LATENT_DECOMPOSITION — 잠재 공간 분해

## 출처
- main.md §3 (잠재 분해, 그룹화된 토큰)
- deep-research-report.md §iVAE·nonlinear ICA·disentanglement (R-4)

## 주장

잠재 공간은 단일 비구조화된 벡터가 아닌 K개의 기능적 하위공간으로 그룹화되어야 합니다.
이것은 의미론적 ground-truth disentanglement(Locatello 불가능성)에 대한 주장이 아니라,
**기능적 그룹화 + 그룹 수준 correction**이 스칼라 수준 correction보다 더 안정적이며,
그룹 할당이 통제된 OOD 변화 하에서 시드 간 일관성이 있다는 주장입니다.

## 수학적 형식화

```
z_t = [z_t^1, ..., z_t^K] ∈ R^{K×d}  [K=6, d=32; 전체 latent = 192]

권장 기능적 그룹 (ground-truth 의미론적 레이블 아님):
  z^1 ∈ R^32  # 로봇 고유감각/동작 하위공간
  z^2 ∈ R^32  # 물체 포즈/속도 하위공간
  z^3 ∈ R^16  # 접촉/상호작용 하위공간
  z^4 ∈ R^16  # 액션-게인/효과 하위공간
  z^5 ∈ R^16  # 컨텍스트/숨겨진 regime 하위공간
  z^6 ∈ R^16  # 보상/목표/태스크-가치 하위공간

그룹에 대한 Attention: α_t ∈ R^K (스칼라 차원 α ∈ R^{K*d}가 아님)
→ 순열 민감도 방지, correction 마스크의 해석 가능성 향상

iVAE 영감을 받은 보조: p(z|u) = Π_k p(z^k|u) 여기서 u = 태스크/도메인 컨텍스트
→ 컨텍스트 변화 하에서 그룹 할당의 식별 가능성 확보 (R-11/I3G)
```

**Locatello 비판**: 보조 신호나 명시적 귀납적 편향 없이, 그룹 인수분해는
근본적으로 식별 불가능합니다. FGLC의 주장:
(1) OOD 유형에 대한 시드 간 기능적 일관성 (경험적 검사)
(2) 그룹별 dynamics 헤드 / 그룹 lasso가 암묵적 분리 가능성 편향 생성
(3) I3G 알고리즘의 경우: 명시적 iVAE 사전 분포가 식별 가능성 강제

## 연결 맵
- 상위: M-4 (encoder가 z_t 생성), R-4 (iVAE/식별 가능성)
- 하위: M-6 (그룹별 dynamics), M-9 (K 그룹에 대한 attention), M-10 (그룹별 correction)
- 알고리즘 링크: R-11 (I3G는 iVAE + ICP를 사용하여 식별 가능한 그룹 생성)

## 체크포인트

- C1 수학적 유효성: CONDITIONAL — Locatello 불가능성은 비지도 학습 경우에 적용됩니다.
  주장은 "기능적 일관성"으로 제한되어야 하며, "ground-truth disentanglement"가 아닙니다.
  iVAE 주장은 태스크 컨텍스트 u를 사용하는 I3G 알고리즘 변형에만 유효합니다.
- C2 신규성: CONDITIONAL — HiP-RSSM은 컨텍스트 조건부 잠재 파라미터를 사용합니다;
  차별화 필요 (K-그룹 기능적 그룹화 vs. 파라미터 추론)
- C3 Reviewer 공격: 높은 위험 — reviewer-2-attack-agent의 공격 3:
  "K=6 그룹화는 자의적입니다." 방어: 기능적이지 의미론적 주장이 아님; 시드 간 일관성.
  검증: 5개 시드에서 OOD 유형별 attention 벡터의 Spearman > 0.7
- C4 타당성: PASS — K=6, d=32는 192차원 잠재 공간; TD-MPC2 기본값과 비슷.
  MLP encoder는 state-only ManiSkill에서 A100에서 실현 가능.
- C5 Claim-지표: CONDITIONAL — K ablation(K=3,6,12)이 K=6 선택 검증에 필요.
  또한: 그룹 안정성을 위한 시드 간 일관성 지표.
- C6 구현 위험: 낮음 — 그룹 분할은 reshape 연산; 특별한 아키텍처 불필요.
- C7 실험 설계: 필수: K ablation sweep + collapsed-K=1 ablation (20_ABLATIONS.md 참조)
- C8 실패 해석: 잠재 그룹 붕괴 (모든 그룹이 동일한 표현 학습)는 그룹 표현 간
  코사인 유사도로 감지; 완화: 그룹별 dynamics 헤드.
- C9 관련 연구: Locatello et al. (2019) PMLR; iVAE Khemakhem et al. (2020) — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = main.md §3. 소비자: 04_BASE_WORLD_MODEL.md, 06_CAUSAL_ATTENTION.md

## 열린 질문
- 올바른 K는 무엇인가? 너무 작으면: 다양한 이동 유형 표현 불가. 너무 크면: attention이 너무 sparse.
- 명시적 그룹 분리 손실이 필요한가, 아니면 그룹별 dynamics 헤드로 충분한가?
- RGB-D 확장 시: 시각적 토큰이 자체 그룹을 갖거나 기존 그룹과 병합되어야 하는가?
