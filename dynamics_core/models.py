from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass(frozen=True)
class Evidence:
    cue: str
    text: str
    meaning: str
    start: int = -1
    end: int = -1


@dataclass
class FeatureReport:
    cues: Dict[str, bool]
    negated: Dict[str, bool]
    evidence: List[Evidence] = field(default_factory=list)
    ignored_matches: List[str] = field(default_factory=list)
    requested_quantity: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class Recommendation:
    primary: str
    scores: Dict[str, int]
    reasons: List[str]
    cautions: List[str]
    steps: List[str]
    combined_methods: List[str] = field(default_factory=list)
    confidence: str = "보통"


@dataclass
class ProblemModel:
    problem_type: str = "일반 동역학 문제"
    analysis_targets: List[str] = field(default_factory=list)
    requested_quantity: str = "자동 추정"
    known_quantities: List[str] = field(default_factory=list)
    motion_state: List[str] = field(default_factory=list)
    forces_present: List[str] = field(default_factory=list)
    forces_ignored: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    conservation_conditions: List[str] = field(default_factory=list)
    coordinate_systems: List[str] = field(default_factory=list)
    allowed_methods: List[str] = field(default_factory=list)
    risky_methods: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class SolutionBlueprint:
    title: str
    fbd_forces: List[str] = field(default_factory=list)
    coordinate_guide: List[str] = field(default_factory=list)
    # 하위 호환용 필드입니다. 4차 개선부터는 applicable_equations를 우선 사용합니다.
    governing_equations: List[str] = field(default_factory=list)
    auxiliary_equations: List[str] = field(default_factory=list)
    application_conditions: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    interpretation_checks: List[str] = field(default_factory=list)
    # 4차 개선: 적용식과 금지식을 분리하여 잘못된 템플릿이 적용식처럼 보이지 않게 합니다.
    applicable_equations: List[str] = field(default_factory=list)
    not_applicable_equations: List[str] = field(default_factory=list)
    cautions: List[str] = field(default_factory=list)
    suppressed_templates: List[str] = field(default_factory=list)
    ambiguity_notes: List[str] = field(default_factory=list)
    support_level: str = "풀이 골격 생성"


@dataclass
class Diagnosis:
    features: FeatureReport
    recommendation: Recommendation
    verdict_title: str
    verdict_body: str
    good_elements: List[str]
    missing_elements: List[str]
    misconception_hits: List[Tuple[str, str]]
    fbd_items: List[str]
    next_questions: List[str]
    problem_model: ProblemModel = field(default_factory=ProblemModel)
    blueprint: SolutionBlueprint = field(default_factory=lambda: SolutionBlueprint(title="기본 풀이 골격"))


@dataclass
class CalcResult:
    ok: bool
    values: Dict[str, Any] = field(default_factory=dict)
    formula: str = ""
    assumptions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
