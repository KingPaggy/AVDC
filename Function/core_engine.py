"""
Re-export from core/orchestrator.py

CoreEngine orchestrates the full scrape/organize workflow without UI references.
"""
from core.orchestrator import CoreEngine, OnLog, OnProgress, OnSuccess, OnFailure  # noqa: F401
