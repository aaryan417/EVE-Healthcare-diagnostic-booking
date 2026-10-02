from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError


def custom_exception_handler(exc, context):
    """
    Custom exception handler that structures error responses predictably
    without destroying DRF field-level validation details or breaking existing test expectations.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_code = getattr(exc, 'default_code', 'error')

        if isinstance(response.data, dict):
            if 'error' not in response.data:
                original_data = dict(response.data)
                message = original_data.get('detail') or "An error occurred."
                if isinstance(message, list) and message:
                    message = str(message[0])

                response.data = {
                    "error": {
                        "code": str(error_code),
                        "message": str(message),
                        "details": original_data
                    }
                }
                # Mirror original keys at top-level for backward compatibility
                for key, val in original_data.items():
                    if key not in response.data:
                        response.data[key] = val
        elif isinstance(response.data, list):
            original_list = list(response.data)
            response.data = {
                "error": {
                    "code": str(error_code),
                    "message": str(original_list[0]) if original_list else "An error occurred.",
                    "details": original_list
                }
            }

    return response
