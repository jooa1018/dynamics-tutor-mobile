from __future__ import annotations

from typing import List, Tuple
import math


def finite_number(name: str, value: float) -> List[str]:
    try:
        if not math.isfinite(float(value)):
            return [f"{name}: 유한한 숫자여야 합니다."]
    except Exception:
        return [f"{name}: 숫자여야 합니다."]
    return []


def positive(name: str, value: float) -> List[str]:
    errors = finite_number(name, value)
    if not errors and value <= 0:
        errors.append(f"{name}: 0보다 커야 합니다.")
    return errors


def non_negative(name: str, value: float) -> List[str]:
    errors = finite_number(name, value)
    if not errors and value < 0:
        errors.append(f"{name}: 음수가 될 수 없습니다.")
    return errors


def coefficient_range(name: str, value: float, low: float = 0.0, high: float = 1.0) -> Tuple[List[str], List[str]]:
    errors = finite_number(name, value)
    warnings: List[str] = []
    if errors:
        return errors, warnings
    if value < low:
        errors.append(f"{name}: {low}보다 작을 수 없습니다.")
    elif value > high:
        warnings.append(f"{name}: 일반적인 학부 동역학 충돌 해석에서는 보통 {low}~{high} 범위를 사용합니다. 특수한 에너지 공급 충돌이 아니라면 값을 다시 확인하세요.")
    return errors, warnings
