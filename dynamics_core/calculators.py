from __future__ import annotations

import math
import re
from typing import Dict, Optional

from sympy import Eq, Symbol, solve

from .models import CalcResult
from .validators import coefficient_range, non_negative, positive

G = 9.81


def solve_constant_acceleration(known: Dict[str, Optional[float]], target: str) -> CalcResult:
    errors = []
    if known.get("t") is not None:
        errors.extend(non_negative("시간 t", float(known["t"])))
    if target not in {"s", "u", "v", "a", "t"}:
        errors.append("구할 값은 s, u, v, a, t 중 하나여야 합니다.")
    if errors:
        return CalcResult(False, errors=errors)

    s, u, v, a, t = [Symbol(x) for x in ["s", "u", "v", "a", "t"]]
    symbols = {"s": s, "u": u, "v": v, "a": a, "t": t}
    equations = [
        Eq(v, u + a * t),
        Eq(s, u * t + a * t**2 / 2),
        Eq(v**2, u**2 + 2 * a * s),
        Eq(s, (u + v) * t / 2),
    ]
    substitutions = {symbols[k]: val for k, val in known.items() if val is not None}
    target_symbol = symbols[target]

    accepted = []
    used = []
    warnings = []

    def consistent(candidate: float) -> bool:
        local = dict(substitutions)
        local[target_symbol] = candidate
        for eq in equations:
            if not eq.free_symbols.issubset(set(local.keys())):
                continue
            try:
                residual = float((eq.lhs - eq.rhs).subs(local))
                if not math.isfinite(residual) or abs(residual) > 1e-6:
                    return False
            except Exception:
                continue
        return True

    rejected_count = 0
    for eq in equations:
        try:
            for item in solve(eq.subs(substitutions), target_symbol):
                val = float(item)
                if not math.isfinite(val):
                    continue
                if target == "t" and val < -1e-9:
                    rejected_count += 1
                    continue
                if consistent(val):
                    if not any(abs(val - x) < 1e-8 for x in accepted):
                        accepted.append(0.0 if abs(val) < 1e-12 else val)
                    used.append(str(eq))
                else:
                    rejected_count += 1
        except Exception:
            continue

    if rejected_count:
        warnings.append("일부 후보해는 다른 입력값과 모순되거나 시간 음수라서 제외했습니다.")
    if len([v for v in known.values() if v is not None]) < 2:
        warnings.append("알려진 값이 너무 적으면 해가 여러 개이거나 결정되지 않을 수 있습니다.")
    if not accepted:
        return CalcResult(False, formula="등가속도 4공식", warnings=warnings, errors=["현재 입력값으로 일관된 해를 찾지 못했습니다."])
    return CalcResult(True, values={target: accepted}, formula="v=u+at, s=ut+1/2at², v²=u²+2as, s=(u+v)t/2", assumptions=["가속도가 일정해야 합니다.", "한 축 방향 부호 기준을 먼저 정해야 합니다."], warnings=warnings)


def projectile_motion(v0: float, angle_deg: float, y0: float = 0.0, g: float = G, air_resistance: bool = False) -> CalcResult:
    errors = []
    errors.extend(non_negative("초기속도 v0", v0))
    errors.extend(positive("중력가속도 g", g))
    if y0 < 0:
        errors.append("초기 높이 y0는 기준 지면보다 아래가 아니라면 0 이상으로 입력하세요. 기준을 다르게 잡은 경우 해석에 주의해야 합니다.")
    if air_resistance:
        return CalcResult(False, errors=["공기저항을 고려하는 조건에서는 표준 포물선 공식 계산기를 그대로 사용할 수 없습니다."], warnings=["drag force 모델, 수치적분, 또는 문제에서 제공한 저항식이 필요합니다."])
    if errors:
        return CalcResult(False, errors=errors)
    theta = math.radians(angle_deg)
    vx = v0 * math.cos(theta)
    vy = v0 * math.sin(theta)
    h_max = y0 + (vy**2 / (2 * g) if vy > 0 else 0.0)
    disc = vy**2 + 2 * g * y0
    if disc < 0:
        return CalcResult(False, errors=["지면 도달 시간을 계산할 수 없습니다. y0와 g를 확인하세요."])
    t_flight = (vy + math.sqrt(disc)) / g
    x_range = vx * t_flight
    warnings = []
    if vy < 0:
        warnings.append("아래 방향으로 던진 경우 최고점은 출발점입니다. vy²/(2g)를 무조건 더하면 안 됩니다.")
    return CalcResult(True, values={"vx": vx, "vy": vy, "최고 높이": h_max, "비행 시간": t_flight, "도달 거리": x_range}, formula="x=vx t, y=y0+vy t-1/2gt²", assumptions=["공기저항을 무시합니다.", "x방향 가속도는 0, y방향 가속도는 -g입니다."], warnings=warnings)


def energy_speed_from_height(height: float, initial_speed: float = 0.0, g: float = G) -> CalcResult:
    errors = []
    errors.extend(non_negative("내려온 높이 h", height))
    errors.extend(non_negative("초기속도 v0", initial_speed))
    errors.extend(positive("중력가속도 g", g))
    if errors:
        return CalcResult(False, errors=errors)
    v = math.sqrt(initial_speed**2 + 2 * g * height)
    return CalcResult(True, values={"v": v}, formula="1/2mv² = 1/2mv0² + mgh", assumptions=["마찰이 없거나 비보존력의 일을 따로 넣지 않는 질점 모델입니다.", "h는 실제로 내려온 높이입니다."], warnings=[])


def circular_min_speed(radius: float, g: float = G) -> CalcResult:
    errors = positive("반지름 R", radius) + positive("중력가속도 g", g)
    if errors:
        return CalcResult(False, errors=errors)
    v = math.sqrt(g * radius)
    return CalcResult(True, values={"v_min": v}, formula="최고점 한계 N=0: mg = mv²/R → v=sqrt(gR)", assumptions=["수직 원운동 최고점에서 접촉을 겨우 유지하는 조건입니다."], warnings=[])


def collision_1d(m1: float, u1: float, m2: float, u2: float, e: float) -> CalcResult:
    errors = positive("m1", m1) + positive("m2", m2)
    e_errors, e_warnings = coefficient_range("반발계수 e", e, 0.0, 1.0)
    errors.extend(e_errors)
    if errors:
        return CalcResult(False, warnings=e_warnings, errors=errors)
    v1 = ((m1 - e * m2) * u1 + (1 + e) * m2 * u2) / (m1 + m2)
    v2 = ((m2 - e * m1) * u2 + (1 + e) * m1 * u1) / (m1 + m2)
    return CalcResult(True, values={"v1": v1, "v2": v2}, formula="m1u1+m2u2=m1v1+m2v2, v2-v1=e(u1-u2)", assumptions=["1차원 충돌입니다.", "충돌 중 외부 충격량을 무시합니다."], warnings=e_warnings)


def rolling_speed_from_height(height: float, beta: float, g: float = G) -> CalcResult:
    errors = non_negative("내려온 높이 h", height) + non_negative("관성계수 β", beta) + positive("중력가속도 g", g)
    if beta > 2:
        errors.append("관성계수 β=I/(mR²)가 너무 큽니다. 일반적인 고리 1, 원판 1/2, 속찬 구 2/5 수준과 비교하세요.")
    if errors:
        return CalcResult(False, errors=errors)
    v = math.sqrt(2 * g * height / (1 + beta))
    return CalcResult(True, values={"v": v}, formula="mgh = 1/2mv² + 1/2Iω², I=βmR², v=ωR", assumptions=["미끄러지지 않는 순수 구름입니다.", "마찰은 정지마찰이며 에너지를 소모하지 않는다고 봅니다."], warnings=[])

# ---------------------------------------------------------------------------
# Beginner numeric helper calculators and unit conversion
# ---------------------------------------------------------------------------

def block_pulley_frictionless(m_a: float, m_b: float, g: float = G) -> CalcResult:
    """Frictionless horizontal block A connected to hanging block B."""
    errors = positive("m_A", m_a) + positive("m_B", m_b) + positive("g", g)
    if errors:
        return CalcResult(False, errors=errors)
    a = m_b * g / (m_a + m_b)
    tension = m_a * a
    return CalcResult(
        True,
        values={"a": a, "T": tension},
        formula="T = m_A a, m_B g - T = m_B a → a = m_B g/(m_A+m_B)",
        assumptions=["마찰 없는 수평면", "질량 없는 줄", "마찰 없는 이상적 도르래", "두 물체의 가속도 크기가 같음"],
        warnings=["자동 정답 생성기가 아니라 대표형 보조 계산기입니다. 문제 조건이 다르면 식이 달라집니다."],
    )


def incline_acceleration(theta_deg: float, mu: float = 0.0, frictionless: bool = True, moving_down: bool = True, g: float = G) -> CalcResult:
    """Simple incline acceleration along the plane for a sliding block."""
    errors = positive("g", g)
    if not (0 <= theta_deg <= 90):
        errors.append("경사각 theta는 0~90도 범위로 입력하세요.")
    if mu < 0:
        errors.append("마찰계수 μ는 음수가 될 수 없습니다.")
    if errors:
        return CalcResult(False, errors=errors)
    theta = math.radians(theta_deg)
    if frictionless:
        a = g * math.sin(theta)
        formula = "mg sinθ = ma → a = g sinθ"
        assumptions = ["마찰 없는 경사면", "아래쪽 경사면 방향을 양의 방향으로 선택"]
    else:
        sign = -1 if moving_down else 1
        a = g * (math.sin(theta) + sign * mu * math.cos(theta))
        formula = "ΣF_parallel = ma, N = mg cosθ, f = μN"
        assumptions = ["물체가 실제로 미끄러지고 있어 운동마찰 모델을 사용", "마찰 방향은 상대운동 반대"]
    return CalcResult(True, values={"a": a}, formula=formula, assumptions=assumptions, warnings=[])


def centripetal_acceleration(radius: float, speed: float | None = None, omega: float | None = None) -> CalcResult:
    errors = positive("반지름 R", radius)
    if speed is None and omega is None:
        errors.append("속력 v 또는 각속도 ω 중 하나를 입력하세요.")
    if speed is not None:
        errors.extend(non_negative("속력 v", speed))
    if omega is not None:
        errors.extend(non_negative("각속도 ω", omega))
    if errors:
        return CalcResult(False, errors=errors)
    if speed is not None:
        an = speed * speed / radius
        return CalcResult(True, values={"a_n": an}, formula="a_n = v²/R", assumptions=["반지름 중심 방향 가속도"], warnings=["구심력은 별도 힘이 아니라 중심 방향 힘의 합입니다."])
    an = omega * omega * radius  # type: ignore[operator]
    return CalcResult(True, values={"a_n": an}, formula="a_n = ω²R", assumptions=["반지름 중심 방향 가속도"], warnings=["구심력은 별도 힘이 아니라 중심 방향 힘의 합입니다."])


def vertical_circle_force(m: float, speed: float, radius: float, position: str = "bottom", force_symbol: str = "T", g: float = G) -> CalcResult:
    errors = positive("질량 m", m) + non_negative("속력 v", speed) + positive("반지름 R", radius) + positive("g", g)
    if position not in {"bottom", "top"}:
        errors.append("position은 'bottom' 또는 'top'만 지원합니다.")
    if errors:
        return CalcResult(False, errors=errors)
    centripetal = m * speed * speed / radius
    if position == "bottom":
        force = m * g + centripetal
        formula = f"{force_symbol} - mg = mv²/R → {force_symbol} = mg + mv²/R"
        assumptions = ["최저점", "중심 방향은 위쪽", "줄 문제면 T, 트랙 문제면 N 사용"]
    else:
        force = centripetal - m * g
        formula = f"{force_symbol} + mg = mv²/R → {force_symbol} = mv²/R - mg"
        assumptions = ["최고점", "중심 방향은 아래쪽", "줄 문제면 T, 트랙 문제면 N 사용"]
    warnings = []
    if force < 0:
        warnings.append("계산된 접촉력/장력이 음수입니다. 줄은 밀 수 없고 트랙 접촉 조건도 다시 확인해야 합니다.")
    return CalcResult(True, values={force_symbol: force}, formula=formula, assumptions=assumptions, warnings=warnings)


def convert_common_units(text: str) -> list[str]:
    """Extract common beginner unit conversions from free text."""
    out: list[str] = []
    for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*g(?=\s|$|[가-힣,.])", text, flags=re.I):
        val = float(m.group(1)) / 1000.0
        out.append(f"{m.group(1)} g = {val:g} kg")
    for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*km/h(?=\s|$|[가-힣,.])", text, flags=re.I):
        val = float(m.group(1)) * 1000.0 / 3600.0
        out.append(f"{m.group(1)} km/h = {val:g} m/s")
    for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*cm(?=\s|$|[가-힣,.])", text, flags=re.I):
        val = float(m.group(1)) / 100.0
        out.append(f"{m.group(1)} cm = {val:g} m")
    for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?)\s*rpm\b", text, flags=re.I):
        val = float(m.group(1)) * 2.0 * math.pi / 60.0
        out.append(f"{m.group(1)} rpm = {val:.3g} rad/s")
    return list(dict.fromkeys(out))
