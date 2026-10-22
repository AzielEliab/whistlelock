/**
 * Crawl files for the WhistleLock download tracker: /llms.txt.
 * Generated from facts already in this Worker (index.js constants, the
 * homepage meta description, and the routes this Worker serves). No new
 * claims. The Zenodo DOI is historical: Zenodo record removed (2026-09-02),
 * so it is printed as text only.
 */

export const CRAWL_META = Object.freeze({
  "name": "WhistleLock",
  "description": "Local drop ledger and dead-man copy by Aziel Eliab; not a mailer.",
  "host": "https://whistlelock-download-tracker.vibelock.workers.dev",
  "github": "https://github.com/AzielEliab/whistlelock",
  "catalog_slug": "whistlelock",
  "doi": null,
  "doi_removed": null,
  "routes": [
    {
      "path": "/download",
      "label": "Counted download (increments the download counter)"
    },
    {
      "path": "/install.sh",
      "label": "One-line installer"
    },
    {
      "path": "/v1/health",
      "label": "Liveness (does not count downloads)"
    },
    {
      "path": "/v1/skill",
      "label": "Agent skill markdown"
    },
    {
      "path": "/openapi.json",
      "label": "OpenAPI"
    },
    {
      "path": "/mcp",
      "label": "MCP pointer"
    },
    {
      "path": "/v1/mesh",
      "label": "Suite mesh status (proxy to aziel-runtime; default OFF)"
    },
    {
      "path": "/ai",
      "label": "How to wire AI assistants"
    }
  ]
});

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

export function llmsTxt(meta = CRAWL_META) {
  const lines = [
    "# " + meta.name,
    "",
    "Author: Aziel Eliab",
    "Identity: Aziel Eliab only.",
    "License: Apache-2.0. Forks welcome.",
    "",
    meta.description,
    "",
    "Homepage: " + meta.host + "/",
  ];
  for (const r of meta.routes) lines.push(r.label + ": " + meta.host + r.path);
  lines.push("Cite: " + meta.host + "/cite.json");
  lines.push("GitHub: " + meta.github);
  lines.push("Catalog: https://aziel-runtime.vibelock.workers.dev/p/" + meta.catalog_slug);
  lines.push("Catalog MCP: POST https://aziel-runtime.vibelock.workers.dev/mcp");
  if (meta.doi) {
    lines.push("");
    lines.push("Historical DOI: " + meta.doi + " (Zenodo record removed (" + meta.doi_removed + "). Not a live record.)");
  }
  lines.push("");
  return lines.join("\n");
}

export function crawlFileResponse(url, request, meta = CRAWL_META) {
  if (request.method !== "GET" && request.method !== "HEAD") return null;
  const p = url.pathname.replace(/\/$/, "") || "/";
  let body = null;
  let type = null;
  if (p === "/llms.txt") {
    body = llmsTxt(meta);
    type = "text/plain; charset=utf-8";
  }
  if (body === null) return null;
  return new Response(request.method === "HEAD" ? null : body, {
    status: 200,
    headers: { "Content-Type": type, "Cache-Control": "public, max-age=300", ...corsHeaders() },
  });
}
