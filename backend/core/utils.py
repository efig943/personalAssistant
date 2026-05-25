"""
core/utils.py
Shared utility functions that are not tied to any single domain.
"""


def deep_update(base_dict: dict, update_dict: dict) -> dict:
    """Recursively deep merge update_dict into base_dict."""
    for key, val in update_dict.items():
        if isinstance(val, dict) and isinstance(base_dict.get(key), dict):
            base_dict[key] = deep_update(base_dict.get(key, {}), val)
        else:
            base_dict[key] = val
    return base_dict
