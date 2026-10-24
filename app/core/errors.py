class ServiceError(Exception):
    """서비스 계층에서 사용하는 API 독립 오류."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
