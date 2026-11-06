"""Shared helpers: code extraction, matching, text classification."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        return json.load(f)


CODE_RE = re.compile(r"A3C\d{9,10}(?!\d)|(?<!\d)\d{10}(?!\d)")


def extract_codes(*texts):
    """Return canonical part codes found in the given strings, in order, de-duplicated.

    'A3C0320410001VD561' -> 'A3C0320410001'; 'HW9815023380' -> '9815023380';
    '9834609880A3C0320410001' -> both codes.
    """
    out = []
    for t in texts:
        if not t:
            continue
        if isinstance(t, (list, tuple)):
            t = " ".join(str(x) for x in t)
        for m in CODE_RE.finditer(str(t).upper()):
            c = m.group(0)
            if c not in out:
                out.append(c)
    return out


def edit_distance_le1(a, b):
    """True when a and b differ by at most one insert, delete or substitution."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) == 1
    if la > lb:
        a, b = b, a
    i = j = diff = 0
    while i < len(a) and j < len(b):
        if a[i] != b[j]:
            diff += 1
            if diff > 1:
                return False
            j += 1
        else:
            i += 1
            j += 1
    return True


def code_match(codes, target):
    """'exact' if target in codes, 'near' if a code is one edit away, else None."""
    if target in codes:
        return "exact"
    for c in codes:
        if c[:3] == target[:3] and edit_distance_le1(c, target):
            return "near"
    return None


ECU_WORDS = re.compile(
    r"centralita|unidad de control|unidad de mando|\becu\b|calculador|calculateur|m[oó]dulo|"
    r"motor ?management|computer|control unit|inyecci|steuerger|ordenador|uce\b|vd56",
    re.I,
)

UNLOCKED_RE = re.compile(
    r"virgen|virgin|vierge|jungfr|immo[\s-]?off|desbloquead|vrij gezet|sin inmovilizador|"
    r"\breset(ead[ao])?\b|unlocked|entsperrt",
    re.I,
)
LOCKED_RE = re.compile(r"(?<!des)bloquead[ao]|\blocked\b|codificad[ao] (al|a su) veh", re.I)
KIT_RE = re.compile(r"\bkit\b|juego|\bset\b|cerradura|lock set|ignition lock|llave", re.I)
ACCIDENT_RE = re.compile(r"siniestr|accidentad|accident|unfall|crash", re.I)
DIESEL_RE = re.compile(r"di[eé]sel|\bhdi\b|bluehdi|\bd-?4d\b|cdti|\btdi\b", re.I)


def classify_immobiliser(text):
    if UNLOCKED_RE.search(text or ""):
        return "unlocked"
    if KIT_RE.search(text or ""):
        return "kit"
    if LOCKED_RE.search(text or ""):
        return "locked"
    return "unknown"
