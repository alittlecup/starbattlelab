"""解题引擎：最低档技巧优先，逐步推进直至解出或卡死。"""

from deduction import Step, Trace

MAX_STEPS = 10000  # 安全上限，防御性


def solve(state, techniques):
    ordered = sorted(techniques, key=_technique_sort_key)
    steps = []
    for _ in range(MAX_STEPS):
        if state.is_solved():
            return Trace(steps=steps, solved=True, stuck_state=None)
        if state.invalid:
            return Trace(steps=steps, solved=False, stuck_state=state)
        progressed = False
        for technique in ordered:
            deduction = technique(state)
            if deduction and deduction.marks:
                state.apply(deduction)
                steps.append(Step.from_deduction(deduction))
                progressed = True
                break
        if not progressed:
            return Trace(steps=steps, solved=False, stuck_state=state)
    return Trace(steps=steps, solved=False, stuck_state=state)


def _technique_sort_key(technique):
    return getattr(technique, "tier", 1)
