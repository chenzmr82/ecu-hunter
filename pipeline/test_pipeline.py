"""Plain-assert tests (no pytest needed): python pipeline/test_pipeline.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import extract_codes, code_match, classify_immobiliser  # noqa: E402

A3C, HW, PSA = "A3C0320410001", "9815023380", "9834609880"

# code extraction
assert extract_codes(["A3C0320410001VD561"]) == [A3C]
assert extract_codes("HW9815023380 x") == [HW]
assert extract_codes("9834609880A3C0320410001") == [PSA, A3C]
assert extract_codes("001001013292E") == []
assert extract_codes("A3C032041001 98346098") == ["A3C032041001"]

# exact vs near
assert code_match([A3C], A3C) == "exact"
assert code_match(["A3C032041001"], A3C) == "near"          # one digit short
assert code_match(["A3C0600500001"], A3C) is None           # different variant
assert code_match(["9835609880"], PSA) == "near"
assert code_match(["9834069880"], PSA) is None              # transposition = 2 edits

# immobiliser wording
assert classify_immobiliser("Computer Motor Management Virgin vrij gezet") == "unlocked"
assert classify_immobiliser("centralita desbloqueada") == "unlocked"
assert classify_immobiliser("kit de gasolina calculadora ECU y bloqueo") == "kit"
assert classify_immobiliser("centralita bloqueada al coche") == "locked"
assert classify_immobiliser("centralita motor uce") == "unknown"

print("ok")
