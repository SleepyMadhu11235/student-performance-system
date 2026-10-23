"""
Shared error-handling infrastructure.

Every error response from this API — whether it's a DRF validation error,
a 404, an AppError raised deliberately by a view, or an unhandled
exception — comes back in the same shape:

    {
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Human readable summary.",
        "details": { ... }   # optional, e.g. per-field validation errors
      }
    }
"""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("predictions")


class AppError(Exception):
    """Raise this anywhere in a view to return a clean, coded JSON error."""

    def __init__(self, message: str, code: str = "APP_ERROR", http_status: int = status.HTTP_400_BAD_REQUEST, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details


def error_envelope(code: str, message: str, details=None) -> dict:
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return payload


def custom_exception_handler(exc, context):
    """
    DRF's REST_FRAMEWORK["EXCEPTION_HANDLER"] hook. Wraps every error path
    (DRF-raised, AppError, or a genuine bug) into the standard envelope
    above and makes sure it's logged.
    """
    view = context.get("view")
    view_name = view.__class__.__name__ if view else "unknown_view"

    if isinstance(exc, AppError):
        logger.warning("AppError in %s: [%s] %s", view_name, exc.code, exc.message)
        return Response(
            error_envelope(exc.code, exc.message, exc.details),
            status=exc.http_status,
        )

    # Let DRF handle anything it recognizes (ValidationError, NotFound,
    # PermissionDenied, MethodNotAllowed, Throttled, etc.) first.
    response = drf_exception_handler(exc, context)

    if response is not None:
        code = _code_for_status(response.status_code)
        message = _extract_message(response.data)
        logger.warning("%s in %s: %s", code, view_name, message)
        response.data = error_envelope(code, message, details=response.data)
        return response

    # Anything else is an unexpected server-side bug — log the full
    # traceback and never leak internals to the client.
    logger.exception("Unhandled exception in %s", view_name, exc_info=exc)
    return Response(
        error_envelope("SERVER_ERROR", "An unexpected error occurred. It has been logged."),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _code_for_status(status_code: int) -> str:
    return {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "THROTTLED",
    }.get(status_code, "ERROR")


def _extract_message(data) -> str:
    """DRF error bodies come in several shapes (list, dict, dict-of-lists).
    Reduce them to one human-readable summary line; the raw shape is still
    available under error.details."""
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    if isinstance(data, list) and data:
        return str(data[0])
    if isinstance(data, dict) and data:
        first_key = next(iter(data))
        first_val = data[first_key]
        first_val = first_val[0] if isinstance(first_val, list) and first_val else first_val
        return f"{first_key}: {first_val}"
    return "Request could not be processed."
