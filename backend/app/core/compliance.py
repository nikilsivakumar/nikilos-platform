"""
The ONE place compliance score gets calculated -- called from the create/
update daily_log endpoint now, and later reused as-is by dashboard
aggregation, weekly summaries, and exports (see DOMAIN_MODEL.md "shared
aggregation logic" convention). Never reimplemented per view.

v1 scoring: simple percentage of targets hit (protein/calories/steps/sleep
each worth 25%), only counting targets that are actually SET on the active
plan -- a user with no calorie target isn't penalized for "missing" it.
This is intentionally simple; refine the weighting later if it doesn't
feel right in practice, but keep it in this one function when you do.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.plans import Plan, PlanMetrics


def calculate_compliance_score(
    db: Session,
    user_id: int,
    weight_kg, calories, protein_g, steps, sleep_hours,
) -> Optional[int]:
    plan = (
        db.query(Plan)
        .filter(Plan.owner_id == user_id, Plan.is_active == True)  # noqa: E712
        .first()
    )
    if plan is None or plan.metrics is None:
        return None  # no active plan/targets -- nothing to score against

    metrics: PlanMetrics = plan.metrics
    checks = []

    if metrics.calorie_target is not None and calories is not None:
        checks.append(calories <= metrics.calorie_target)
    if metrics.protein_target is not None and protein_g is not None:
        checks.append(protein_g >= metrics.protein_target)
    if metrics.step_target is not None and steps is not None:
        checks.append(steps >= metrics.step_target)
    if metrics.sleep_target is not None and sleep_hours is not None:
        checks.append(sleep_hours >= metrics.sleep_target)

    if not checks:
        return None  # plan has targets, but nothing loggable matched today

    return round(100 * sum(checks) / len(checks))