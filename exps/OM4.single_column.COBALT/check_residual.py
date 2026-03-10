"""
Very basic script used to ensure that abs(val) is not > tol.
Used in the 1D BGC test to ensure that tracer budgets close.
Usage: check_residual.py val [tol]
"""
import sys

val = float(sys.argv[1])
tol = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0e-17
if abs(val) > tol:
    print(f'ERROR: residual too large: {val}')
    sys.exit(1)
print(f'OK: residual = {val}')