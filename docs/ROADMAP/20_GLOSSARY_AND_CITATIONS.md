# 용어 사전 및 인용 원장

## 용어 SSoT (반드시 보존되어야 하는 용어)

이 용어들은 여기서 정의됩니다. 어떤 코드, 문서, 논문 섹션에서도 이름을 바꾸지 마십시오.

| 용어 | 정의 |
|---|---|
| falsification gate | 예측 분포가 관측과 통계적으로 불일치할 때 감지하는 보정된 sigmoid MLP β_t |
| standardized mismatch (표준화된 불일치) | ρ_t = Σ_t^{-1/2}(z_{t+1}-μ_t); 기본 WM 하에서 그룹별 정규화된 잔차 |
| latent group (잠재 그룹) | K개의 기능적 잠재 하위공간 z^k ∈ R^d 중 하나; ground-truth 의미론적 팩터 아님 |
| intervention-policy attention (개입 정책 attention) | α_t; 보정 개입 정책으로 검증된 그룹 수준 sparse attention (인과적 귀인자 아님) |
| sparse correction (sparse 보정) | μ̃_t^k = μ_t^k + β_t α_t^k δ_t^k; 선택된 그룹에만 적용, 밀집 잔차 업데이트 아님 |
| necessity (필요성) | L_nec: 선택된 마스크 제거 시 성능 저하 |
| sufficiency (충분성) | L_suf: 선택된 마스크만으로 거의 완전한 보정 성능 달성 |
| counterfactual rollout (반사실적 rollout) | 보정 선택 검증을 위해 대안적 물리적 파라미터 하에서 rollout |
| robust MPC | 분포적 강인성이 있는 보정된 dynamics 하에서 MPPI/CEM planning |
| decision-relevant compute (결정 관련 계산) | action/value 변화가 계산 비용을 정당화할 때만 planning 호출 |
| action-relevance (action 관련성) | Correction 대상은 NLL만이 아닌 value/action 개선 |
| wrong-dynamics-hypothesis persistence | 잘못된 물리적 dynamics가 falsification 증거 후 유지되는 시간 |

## 인용 원장 (≥2개 출처 규칙)

모든 인용은 포함 전에 확인된 ≥2개의 출처 URL이 필요합니다.
상태: MCP 교차 검증 대기 중. docs/orchestration/mcp_research/INDEX.md 참조.

| 참조 | arXiv | Semantic Scholar | 상태 |
|---|---|---|---|
| TD-MPC2 (Hansen 2024) | 2310.16828 | 미정 | 대기 중 |
| DreamerV3 (Hafner 2023) | 2301.04104 | 미정 | 대기 중 |
| HiP-RSSM (Achterhold 2022) | 2206.14697 | 미정 | 대기 중 |
| PLSM (Tomar 2024) | 2401.17835 | 미정 | 대기 중 |
| Jain & Wallace 2019 | arXiv | 미정 | 대기 중 |
| Wiegreffe & Pinter 2019 | arXiv | 미정 | 대기 중 |
| Khemakhem 2020 iVAE | 1907.04809 | 미정 | 대기 중 |
| Locatello 2019 | PMLR v97 | 미정 | 대기 중 |
| Peters 2016 ICP | arXiv | 미정 | 대기 중 |
| Arjovsky 2019 IRM | arXiv | 미정 | 대기 중 |
| Angelopoulos 2022 CRC | arXiv | 미정 | 대기 중 |
| Koh & Liang 2017 | 1703.04730 | 미정 | 대기 중 |
| Frye 2020 ASV | arXiv | 미정 | 대기 중 |
| ManiSkill v3 | 2410.00425 | 미정 | 대기 중 |
| DROID (Khazatsky 2024) | 2403.12945 | 미정 | 대기 중 |
| BridgeData V2 (Walke 2023) | 2308.12952 | 미정 | 대기 중 |

주: 이 원장은 22_NOVELTY_AND_THREATS.md의 MCP 교차 검증에서 채워집니다.
