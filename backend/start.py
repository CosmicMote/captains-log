#!/usr/bin/env python3
"""Start the Captain's Log backend server.

Automatically uses HTTPS when SSL has been configured via generate_cert.py
or configure_ssl.py. Falls back to HTTP if no SSL config is present.

Run from the backend directory:
    python start.py
"""

import uvicorn
import auth_config

HOST = "127.0.0.1"
PORT = 8000


def main() -> None:
    ssl = auth_config.get_ssl_config()

    kwargs = dict(app="main:app", host=HOST, port=PORT, reload=True)

    if ssl:
        kwargs["ssl_certfile"] = ssl["certfile"]
        kwargs["ssl_keyfile"]  = ssl["keyfile"]
        scheme = "https"
    else:
        scheme = "http"

    url = f"{scheme}://{HOST}:{PORT}"
    print(f"Starting Captain's Log at {url}")

    if not ssl:
        print("Tip: run generate_cert.py or configure_ssl.py to enable HTTPS.")

    uvicorn.run(**kwargs)


if __name__ == "__main__":
    main()
