import json
import sys
import urllib.request

URL = "https://online-exam-portal-6nxf.onrender.com/health"


def main() -> int:
    try:
        with urllib.request.urlopen(URL, timeout=15) as response:
            body = response.read().decode("utf-8")
            status = response.getcode()
        data = json.loads(body)
        if status == 200 and data.get("status") == "ok":
            print("Health check passed")
            return 0
        print(f"Unexpected health response: status={status}, body={body}")
        return 1
    except Exception as exc:
        print(f"Health check failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
