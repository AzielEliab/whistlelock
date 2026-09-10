# whistlelock-download-tracker

Isolated Cloudflare Worker for WhistleLock counted downloads.

KV: `WHISTLELOCK_DOWNLOADS` bound as `DOWNLOADS`. Not mixed with FoldLock or any other product.

`/download` serves the gzip via ASSETS (HTTP 200). No 302 to GitHub.
`/v1` never increments. Hosted never holds whistle files. Not a mailer.
`/v1/mesh/*` PROXY to aziel-runtime suite mesh (`AZIEL_RUNTIME` / `https://aziel-runtime.vibelock.workers.dev`). Default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 packet transfer is a hub cite / Worker mesh cross-map only (local qnsd in [qnm-node](https://github.com/AzielEliab/qnm-node); runtime cites + catalog `mesh` field in [aziel-runtime](https://github.com/AzielEliab/aziel-runtime); pair custody on [AZInterface](https://github.com/AzielEliab/azinterface)). Not a Softwares-tab product. No public qnsd proxy. No Node Gate. No auto-heal. Not anonymity. Human UI Live Nodes strip polls `GET /v1/mesh`.

Verify: `curl -sS -A 'Mozilla/5.0' https://whistlelock-download-tracker.vibelock.workers.dev/v1/mesh/status` returns MESH-OK style JSON with `enabled: false` by default.

Host: https://whistlelock-download-tracker.vibelock.workers.dev
