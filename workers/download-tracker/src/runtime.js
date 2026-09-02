/**
 * WhistleLock hosted runtime. Preview hashes only; never store drops or packets.
 * /v1 never touches DOWNLOADS KV. Not a mailer.
 */
const PRODUCT = "whistlelock";
const VERSION = "0.1.0";
const SPEC = "whistlelock-v0";
const HOST = "https://whistlelock-download-tracker.vibelock.workers.dev";
const CATALOG = "https://aziel-runtime.vibelock.workers.dev";
const GENESIS_PREV = "0".repeat(64);
const PROTOCOL = "2025-03-26";
const LIMITATION =
  "THIS IS: local directory store + TemporalLock-shaped rows + local dead-man copy + optional refresh of an operator-supplied source_url at verify. THIS IS NOT: rotating encrypted identity mailbox; IP-masking/proxy; mixnet/anonymous relay; boot scraper of inboxes; a public website; UL; FoldLock; EmployeeLock; GodLock; legal advice. Hosted API never holds whistle files. Not a mailer.";

const HASHED_FIELDS = [
  "drop_id",
  "entry_id",
  "kind",
  "payload_sha256",
  "prev_hash",
  "source_note",
  "summary",
  "timestamp",
];

const SKILL_MD = "---\nname: WhistleLock\ndescription: Use this when someone already has a whistle file and needs a local hashed drop ledger plus a local dead-man copy. Not a mailer. Hosted /v1 never stores drops.\n---\n\n# WhistleLock skill\n\nWhistleLock is a **local folder** that copies a file you already have, hashes it, and chains the row. If you stop checking in, it copies a packet you already placed into `released/`. **It does not mail.** It does not rotate From: addresses. It does not hide your IP. It does not scrape inboxes.\n\nCall it when:\n\n- the operator already holds a file (a `.eml` they saved, a PDF, a note) and wants a hashed drop;\n- they want a dead-man **copy on this machine**, not a send path.\n\nDo **not** call it to send anonymous mail, mask IP, hunt inboxes, or store whistle files on the hosted Worker.\n\nAuthor: **Aziel Eliab**. Apache-2.0. Paper WL-WP-0.1. DOI [10.5281/zenodo.22257762](https://doi.org/10.5281/zenodo.22257762) (that preprint also covers FoldLock; this product is WhistleLock only).\n\n## Hosted /v1 never stores drops\n\nThe Worker is a counted download + a preview API.\n\n- `GET /v1/health` \u2014 liveness. Does not increment downloads.\n- `POST /v1/hash-preview` \u2014 SHA-256 of posted bytes. **Not stored.**\n- `POST /v1/canon-preview` \u2014 hash a proposed ledger row. **Not stored.**\n- `GET /v1/skill` \u2014 this markdown. Does not increment downloads.\n\nHosted never holds whistle files. Hosted is not a mailer.\n\nAlways send `User-Agent: Mozilla/5.0`. Cloudflare Workers may 403 empty agents.\n\n## OpenAPI and MCP\n\n- This Worker OpenAPI: https://whistlelock-download-tracker.vibelock.workers.dev/openapi.json\n- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json\n- MCP: `POST https://whistlelock-download-tracker.vibelock.workers.dev/mcp`\n- Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`\n\nGrok: import the OpenAPI as a custom tool. ChatGPT: GPT Actions \u2192 Import from URL. Venice: HTTP tools.\n\nCounted install (this Worker, HTTP 200 gzip, no 302 to GitHub):\n\n```bash\ncurl -fsSL https://whistlelock-download-tracker.vibelock.workers.dev/install.sh | bash\n```\n\nThen `whistlelock ui` \u2192 http://127.0.0.1:8873 (loopback only). Tap **Init / Drop / Check in / Arm / Tick / Verify**. Dead-man copy is local. Does not mail.\n\n## Honest one-liner\n\nTHIS IS a local vault + chained rows + local dead-man copy. THIS IS NOT a mailer, mixnet, IP mask, inbox scraper, UL, FoldLock, EmployeeLock, or GodLock.\n\nForks are welcome and always allowed.\n";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Protocol-Version, mcp-session-id",
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders() },
  });
}

function html(body) {
  return new Response(body, {
    headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders() },
  });
}

function originOf(request) {
  try {
    return new URL(request.url).origin;
  } catch {
    return HOST;
  }
}

function asStr(v) {
  if (v == null) return "";
  return String(v);
}

function canonicalJson(fields) {
  const payload = {};
  for (const key of HASHED_FIELDS) payload[key] = asStr(fields[key]);
  const keys = Object.keys(payload).sort();
  return "{" + keys.map((k) => JSON.stringify(k) + ":" + JSON.stringify(payload[k])).join(",") + "}";
}

async function sha256Hex(data) {
  const buf = typeof data === "string" ? new TextEncoder().encode(data) : data;
  const digest = await crypto.subtle.digest("SHA-256", buf);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function pickFields(body) {
  const src = body && typeof body === "object" ? body : {};
  const row = src.row && typeof src.row === "object" ? src.row : src;
  return {
    entry_id: asStr(row.entry_id || "WL-0001"),
    timestamp: asStr(row.timestamp || ""),
    kind: asStr(row.kind || "drop"),
    summary: asStr(row.summary || "sample drop"),
    drop_id: asStr(row.drop_id || ""),
    payload_sha256: asStr(row.payload_sha256 || ""),
    source_note: asStr(row.source_note || ""),
    prev_hash: asStr(row.prev_hash || GENESIS_PREV),
  };
}

async function hashPreview(request) {
  const ctype = (request.headers.get("content-type") || "").toLowerCase();
  let bytes;
  if (ctype.includes("application/json")) {
    let body;
    try {
      body = await request.json();
    } catch {
      return { error: "JSON body required", stored: false, limitation: LIMITATION };
    }
    if (body && typeof body === "object" && (body.b64 || body.bytes_b64)) {
      const raw = String(body.b64 || body.bytes_b64);
      const bin = atob(raw);
      bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
    } else if (body && typeof body === "object" && body.text != null) {
      bytes = new TextEncoder().encode(String(body.text));
    } else {
      bytes = new TextEncoder().encode(JSON.stringify(body));
    }
  } else {
    bytes = new Uint8Array(await request.arrayBuffer());
  }
  const digest = await sha256Hex(bytes);
  return {
    product: PRODUCT,
    version: VERSION,
    spec: SPEC,
    kv_increment: false,
    stored: false,
    limitation: LIMITATION,
    bytes: bytes.byteLength,
    sha256: digest,
  };
}

async function canonPreview(body) {
  const fields = pickFields(body || {});
  if (!fields.timestamp) {
    fields.timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  }
  const canonical = canonicalJson(fields);
  const digest = await sha256Hex(canonical);
  return {
    product: PRODUCT,
    version: VERSION,
    spec: SPEC,
    kv_increment: false,
    stored: false,
    limitation: LIMITATION,
    fields,
    canonical,
    row_hash: digest,
    genesis: fields.prev_hash === GENESIS_PREV,
  };
}

function openapiSpec(origin) {
  return {
    openapi: "3.1.0",
    info: {
      title: "WhistleLock runtime",
      version: VERSION,
      summary: "Local drop ledger preview. Not a mailer. Hosted never holds whistle files.",
      description: LIMITATION,
      license: { name: "Apache-2.0", identifier: "Apache-2.0" },
      contact: { name: "Aziel Eliab", url: "https://github.com/AzielEliab/whistlelock" },
    },
    servers: [{ url: origin }],
    paths: {
      "/v1/health": {
        get: {
          operationId: "whistlelock_health",
          summary: "Liveness. Does not increment download KV. Hosted never holds whistle files.",
          responses: { "200": { description: "ok" } },
        },
      },
      "/v1/hash-preview": {
        post: {
          operationId: "whistlelock_hash-preview",
          summary: "SHA-256 of posted bytes. Not stored. Hosted never holds whistle files.",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: { type: "object" },
                example: { text: "sample drop" },
              },
              "application/octet-stream": { schema: { type: "string", format: "binary" } },
            },
          },
          responses: { "200": { description: "sha256" } },
        },
      },
      "/v1/canon-preview": {
        post: {
          operationId: "whistlelock_canon-preview",
          summary: "Hash a proposed ledger row. Not stored. Not a mailer.",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: { type: "object" },
                example: { summary: "sample drop", kind: "drop", prev_hash: GENESIS_PREV },
              },
            },
          },
          responses: { "200": { description: "canonical + row_hash" } },
        },
      },
      "/v1/skill": {
        get: {
          operationId: "whistlelock_skill",
          summary: "Return WhistleLock skill markdown. Does not increment download KV.",
          responses: { "200": { description: "markdown" } },
        },
      },
    },
  };
}

function aiHtml(origin) {
  return `<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>WhistleLock — AI runtime</title>
<style>
  :root { color-scheme: dark; }
  body { font: 16px/1.45 system-ui, sans-serif; max-width: 44rem; margin: 3rem auto; padding: 0 1.25rem; background: #0e1014; color: #e8eaef; }
  a { color: #c9d4ff; }
  .banner { border: 1px solid #5c4a1a; background: #241c0d; color: #f0d78c; padding: .85rem 1rem; border-radius: 8px; }
  pre { background: #151922; padding: .85rem 1rem; overflow: auto; border-radius: 8px; }
</style>
<body>
<h1>WhistleLock runtime</h1>
<p class="banner">${LIMITATION}</p>
<p>OpenAPI: <a href="${origin}/openapi.json">${origin}/openapi.json</a></p>
<p>Skill: <a href="${origin}/v1/skill">${origin}/v1/skill</a></p>
<p>MCP: POST <code>${origin}/mcp</code> · Catalog: <a href="${CATALOG}/">${CATALOG}</a></p>
<pre>curl -A Mozilla/5.0 ${origin}/v1/health
curl -A Mozilla/5.0 -X POST ${origin}/v1/hash-preview -H 'content-type: application/json' \\
  -d '{"text":"sample drop"}'
curl -A Mozilla/5.0 -X POST ${origin}/v1/canon-preview -H 'content-type: application/json' \\
  -d '{"summary":"sample drop","kind":"drop"}'</pre>
<p>GET/POST under <code>/v1</code> never increment the download counter. Hosted never holds whistle files. Not a mailer.</p>
<p><a href="/">Downloads</a></p>
</body></html>`;
}

function mcpTools() {
  return [
    { name: "whistlelock_health", description: "Liveness. Does not increment download KV. Hosted never holds whistle files.", inputSchema: { type: "object" } },
    {
      name: "whistlelock_hash-preview",
      description: "SHA-256 of posted bytes. Not stored. Hosted never holds whistle files. Not a mailer.",
      inputSchema: { type: "object", additionalProperties: true },
    },
    {
      name: "whistlelock_canon-preview",
      description: "Hash a proposed ledger row. Not stored. Not a mailer.",
      inputSchema: { type: "object", additionalProperties: true },
    },
    {
      name: "whistlelock_skill",
      description: "Return WhistleLock skill markdown. Does not increment download KV.",
      inputSchema: { type: "object" },
    },
  ];
}

async function handleMcp(request) {
  if (request.method === "GET") {
    return json({
      ok: true,
      transport: "JSON-RPC MCP-over-HTTP",
      endpoint: "POST /mcp",
      methods: ["initialize", "tools/list", "tools/call", "ping"],
      auth: "none (public)",
      limitation: LIMITATION,
    });
  }
  if (request.method !== "POST") return json({ error: "POST JSON-RPC to /mcp" }, 405);
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } });
  }
  const id = body && body.id !== undefined ? body.id : null;
  const method = body && body.method;
  const params = (body && body.params) || {};
  const result = (value) => json({ jsonrpc: "2.0", id, result: value });
  if (method === "initialize") {
    return result({
      protocolVersion: PROTOCOL,
      capabilities: { tools: { listChanged: false } },
      serverInfo: { name: PRODUCT, version: VERSION },
      instructions: LIMITATION,
    });
  }
  if (method === "notifications/initialized" || method === "initialized") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }
  if (method === "ping") return result({});
  if (method === "tools/list") return result({ tools: mcpTools() });
  if (method === "tools/call") {
    const name = params.name;
    const args = params.arguments || params.input || {};
    let payload;
    if (name === "whistlelock_health") {
      payload = { ok: true, product: PRODUCT, version: VERSION, kv_increment: false, stored: false, limitation: LIMITATION };
    } else if (name === "whistlelock_hash-preview") {
      const text = args.text != null ? String(args.text) : JSON.stringify(args);
      const digest = await sha256Hex(text);
      payload = { product: PRODUCT, stored: false, sha256: digest, bytes: new TextEncoder().encode(text).byteLength, limitation: LIMITATION };
    } else if (name === "whistlelock_canon-preview") {
      payload = await canonPreview(args);
    } else if (name === "whistlelock_skill") {
      payload = { markdown: SKILL_MD };
    } else {
      payload = { error: "unknown tool", name };
    }
    return result({ content: [{ type: "text", text: JSON.stringify(payload) }], isError: Boolean(payload.error) });
  }
  return json({ jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } });
}

export async function handleRuntimeApi(request, url) {
  const path = url.pathname.replace(/\/+$/, "") || "/";
  if (path === "/mcp") return handleMcp(request);
  if (path === "/v1/health" && request.method === "GET") {
    return json({
      ok: true,
      product: PRODUCT,
      version: VERSION,
      spec: SPEC,
      runtime: true,
      kv_increment: false,
      stored: false,
      limitation: LIMITATION,
      catalog: CATALOG,
      author: "Aziel Eliab",
      mails: false,
    });
  }
  if (path === "/v1/skill" && request.method === "GET") {
    return new Response(SKILL_MD, {
      status: 200,
      headers: { "Content-Type": "text/markdown; charset=utf-8", "Cache-Control": "private, no-store", ...corsHeaders() },
    });
  }
  if (path === "/openapi.json" && request.method === "GET") {
    return json(openapiSpec(originOf(request)));
  }
  if ((path === "/ai" || url.pathname === "/ai/") && request.method === "GET") {
    return html(aiHtml(originOf(request)));
  }
  if (path === "/v1/hash-preview" && request.method === "POST") {
    return json(await hashPreview(request));
  }
  if (path === "/v1/canon-preview" && request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "JSON body required", limitation: LIMITATION, stored: false }, 400);
    }
    return json(await canonPreview(body));
  }
  if (path.startsWith("/v1/") || path === "/v1") {
    return json({ error: "not found", hint: "GET /v1/health  GET /v1/skill  POST /v1/hash-preview  POST /v1/canon-preview", limitation: LIMITATION }, 404);
  }
  return null;
}
