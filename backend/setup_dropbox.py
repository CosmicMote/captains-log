#!/usr/bin/env python3
"""
Interactive CLI to configure Dropbox OAuth credentials for Captain's Log.

Steps:
  1. Create a Dropbox app at https://www.dropbox.com/developers/apps
       - Choose "Scoped access" → "Full Dropbox" (or "App folder")
       - Under Permissions, enable: files.content.write
  2. Copy the App Key and App Secret from the app's Settings tab
  3. Run this script and follow the prompts

The resulting refresh token is saved to auth_config.json.
You can then set the backup password and schedule in the app's Settings UI.
"""

import sys
import webbrowser

from dropbox import DropboxOAuth2FlowNoRedirect

import auth_config


def main() -> None:
    print("╔══════════════════════════════════════════╗")
    print("║  Captain's Log — Dropbox Setup           ║")
    print("╚══════════════════════════════════════════╝")
    print()
    print("You need a Dropbox app with 'files.content.write' permission.")
    print("Create one at: https://www.dropbox.com/developers/apps")
    print()

    app_key    = input("App Key:    ").strip()
    app_secret = input("App Secret: ").strip()

    if not app_key or not app_secret:
        print("Error: App Key and App Secret are both required.")
        sys.exit(1)

    flow = DropboxOAuth2FlowNoRedirect(
        app_key,
        app_secret,
        token_access_type="offline",
    )
    auth_url = flow.start()

    print()
    print("Open this URL in your browser to grant access:")
    print()
    print(f"  {auth_url}")
    print()

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass  # best-effort

    auth_code = input("Paste the authorization code shown by Dropbox: ").strip()
    if not auth_code:
        print("Error: No authorization code provided.")
        sys.exit(1)

    try:
        result = flow.finish(auth_code)
    except Exception as e:
        print(f"Error: Authorization failed — {e}")
        sys.exit(1)

    # Preserve any existing Dropbox settings (path, interval, password)
    existing = auth_config.get_dropbox_config() or {}
    existing.update({
        "app_key":       app_key,
        "app_secret":    app_secret,
        "refresh_token": result.refresh_token,
    })
    auth_config.set_dropbox_config(existing)

    print()
    print("✓ Dropbox credentials saved.")
    print("  Open the app's Settings to set a backup password and schedule.")


if __name__ == "__main__":
    main()
