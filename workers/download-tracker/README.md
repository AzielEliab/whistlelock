# whistlelock-download-tracker

Isolated Cloudflare Worker for WhistleLock counted downloads.

KV: `WHISTLELOCK_DOWNLOADS` bound as `DOWNLOADS`. Not mixed with FoldLock or any other product.

`/download` serves the gzip via ASSETS (HTTP 200). No 302 to GitHub.
`/v1` never increments. Hosted never holds whistle files. Not a mailer.
