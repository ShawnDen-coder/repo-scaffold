"""Constants module for application-wide configuration values.

This module centralizes all constant definitions used throughout the application.
All configuration values, magic numbers, and fixed strings should be defined here
to maintain a single source of truth.

Typical usage example:

    from {{cookiecutter.project_slug}}.constants import MAX_RETRIES, DEFAULT_TIMEOUT

    if retry_count < MAX_RETRIES:
        perform_operation(timeout=DEFAULT_TIMEOUT)

Attributes:
    Values will be defined here as uppercase constants following Python naming conventions.
"""