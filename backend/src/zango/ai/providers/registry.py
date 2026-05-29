"""
Global registry of available LLM provider classes.
Provider classes register themselves on import via the @register_provider decorator.
The registry is provider_slug -> ProviderClass mapping.
"""

from zango.ai.exceptions import ProviderNotFound


PROVIDER_REGISTRY: dict[str, type] = {}


def register_provider(slug: str, display_name: str, icon: str = None):
    """
    Class decorator that registers a provider class in the global registry.

    Usage:
        @register_provider("anthropic", "Anthropic", icon="anthropic.svg")
        class AnthropicProvider(BaseLLMProvider):
            ...
    """

    def decorator(cls):
        cls.slug = slug
        cls.display_name = display_name
        cls._icon = icon
        PROVIDER_REGISTRY[slug] = cls
        return cls

    return decorator


def get_provider_class(slug: str):
    """Look up a provider class by slug. Raises ProviderNotFound if not registered."""
    if slug not in PROVIDER_REGISTRY:
        raise ProviderNotFound(slug)
    return PROVIDER_REGISTRY[slug]


def get_available_providers() -> list[dict]:
    """
    Returns metadata about all registered providers for the App Panel UI.
    Each entry includes: slug, display_name, icon, supported_models,
    config_fields.
    """
    providers = []
    for slug, cls in PROVIDER_REGISTRY.items():
        providers.append(
            {
                "slug": cls.slug,
                "display_name": cls.display_name,
                "icon": getattr(cls, "_icon", None),
                "supported_models": getattr(cls, "supported_models", []),
                "config_fields": getattr(cls, "config_fields", []),
            }
        )
    return providers
