# Browser Extension

This extension sends completed Chess.com games to the local API at `http://127.0.0.1:8000`.

## Usage

1. Start the backend.
2. Load this folder as an unpacked extension in Chromium.
3. Open a completed Chess.com game or analysis page.
4. Click the extension action.

If the backend is offline, the extension stores the payload in `chrome.storage.local` and retries it the next time the action succeeds.
