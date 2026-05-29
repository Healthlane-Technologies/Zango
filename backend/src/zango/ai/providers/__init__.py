"""
Provider autodiscovery.
Each provider module registers itself via @register_provider on import.
Missing SDK dependencies are silently skipped.
"""

try:
    from . import anthropic  # noqa: F401
except ImportError:
    pass

try:
    from . import openai  # noqa: F401
except ImportError:
    pass

try:
    from . import azure_openai  # noqa: F401
except ImportError:
    pass

try:
    from . import bedrock  # noqa: F401
except ImportError:
    pass
