"""
Normalisation module for the ETL pipeline.
Re-exports utilities and provides higher-level normalisation helpers if needed.
"""

from .utils import normalize_dataframe

__all__ = ["normalize_dataframe"]