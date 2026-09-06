"""
US Navy method body fat % estimate -- calculated on demand, never stored.
This is an ESTIMATE from circumference measurements, not a substitute for
DEXA/calipers/BIA. If a measurement has body_fat_pct_manual set (a real
scan/scale reading), prefer that over this calculation -- see
app/models/body_measurements.py.
"""

import math
from decimal import Decimal
from typing import Optional

from app.models.users import BiologicalSex


def calculate_navy_body_fat_pct(
    sex: Optional[BiologicalSex],
    height_cm: Optional[Decimal],
    neck_cm: Optional[Decimal],
    waist_cm: Optional[Decimal],
    hip_cm: Optional[Decimal] = None,
) -> Optional[float]:
    """Returns None if sex or any required measurement for that sex is missing -- never guesses."""
    if sex is None or height_cm is None or neck_cm is None or waist_cm is None:
        return None

    height = float(height_cm)
    neck = float(neck_cm)
    waist = float(waist_cm)

    if sex == BiologicalSex.male:
        if waist <= neck:
            return None  # formula requires waist > neck; invalid input, don't produce a nonsense number
        bf = 495 / (1.0324 - 0.19077 * math.log10(waist - neck) + 0.15456 * math.log10(height)) - 450
    else:
        if hip_cm is None:
            return None
        hip = float(hip_cm)
        if (waist + hip) <= neck:
            return None
        bf = 495 / (1.29579 - 0.35004 * math.log10(waist + hip - neck) + 0.22100 * math.log10(height)) - 450

    return round(bf, 1)