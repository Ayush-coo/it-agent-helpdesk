from collections import Counter

_REQUESTS: Counter[tuple[str, str, str]] = Counter()


def record_request(method: str, path: str, status_code: int) -> None:
    _REQUESTS[(method, path, str(status_code))] += 1


def prometheus_text() -> str:
    lines = [
        "# HELP localops_http_requests_total HTTP requests handled by the API.",
        "# TYPE localops_http_requests_total counter",
    ]
    for (method, path, status), count in sorted(_REQUESTS.items()):
        lines.append(
            f'localops_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
        )
    return "\n".join(lines) + "\n"
