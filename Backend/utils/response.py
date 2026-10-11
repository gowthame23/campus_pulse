from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi.responses import JSONResponse

def api_response(
    success: bool = True,
    message: str = "Success",
    data: Optional[Any] = None,
    errors: Optional[List[Dict[str, Any]]] = None,
    status_code: int = 200,
) -> JSONResponse:
    payload = {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if errors:
        payload["errors"] = errors
    return JSONResponse(status_code=status_code, content=payload)
