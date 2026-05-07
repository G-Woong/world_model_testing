"""falsifiable_regime_world_model — NeurIPS 2026 메인트랙 코드 패키지.

본 패키지는 다음을 포함한다.
    rg4f/       RegimeGrid-4Room Factorized Tasks 환경 (Session 2)
    (이후 세션에서 dataset / model / planner 등이 추가된다)

본 ``__init__.py``는 외부에 노출할 API를 명시적으로 import 하지 않는다.
사용자가 필요한 서브패키지를 직접 import하도록 한다 (lazy / explicit import).
"""

__version__ = "0.1.0-session2"
