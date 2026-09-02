/* WhistleLock UI. No CDN. No telemetry. Does not mail. */
(function () {
  const kid = document.getElementById("kid-plain");
  const verifyLine = document.getElementById("verify-line");
  const deadmanLine = document.getElementById("deadman-line");
  const rowsPre = document.getElementById("rows-pre");
  const advancedPanel = document.getElementById("advanced-panel");
  const viewSimple = document.getElementById("view-simple");
  const viewAdvanced = document.getElementById("view-advanced");
  const dropFile = document.getElementById("drop-file");
  const packetFile = document.getElementById("packet-file");

  let advanced = false;
  document.body.classList.add("simple");

  function setView(next) {
    advanced = next;
    document.body.classList.toggle("simple", !advanced);
    viewSimple.classList.toggle("on", !advanced);
    viewAdvanced.classList.toggle("on", advanced);
    viewSimple.setAttribute("aria-pressed", String(!advanced));
    viewAdvanced.setAttribute("aria-pressed", String(advanced));
    advancedPanel.hidden = !advanced;
  }

  function paint(state) {
    const c = (state && state.counts) || {};
    document.getElementById("c-drops").textContent = c.drops || 0;
    document.getElementById("c-rows").textContent = c.rows || 0;
    document.getElementById("c-armed").textContent = c.armed || 0;
    const dm = (state && state.deadman) || {};
    document.getElementById("c-window").textContent = dm.interval_hours || "—";
    document.getElementById("c-released").textContent = c.released || 0;
    document.getElementById("c-ok").textContent = c.chain_ok || 0;
    const v = (state && state.verify) || {};
    const ok = v.ok === true;
    kid.textContent = ok
      ? "Chain hashes. Dead-man copy is local. WhistleLock did not mail anything."
      : ("Chain did not hash. " + ((v.errors && v.errors[0]) || (v.missing_files && v.missing_files[0]) || "Verify failed."));
    verifyLine.textContent = v.ok === undefined
      ? ""
      : ("ok=" + v.ok + " rows=" + v.rows + " missing=" + ((v.missing_files || []).length));
    deadmanLine.textContent = "armed=" + Boolean(dm.armed) +
      " interval_hours=" + (dm.interval_hours || 0) +
      " last_checkin=" + (dm.last_checkin || "none") +
      " released=" + Boolean(dm.released) +
      " (local copy only; does not mail)";
    rowsPre.textContent = JSON.stringify({
      drops: state && state.drops,
      rows: state && state.rows,
      deadman: dm,
      released_dirs: state && state.released_dirs
    }, null, 2);
  }

  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body == null ? "{}" : body
    }).then(function (res) {
      return res.json().then(function (j) {
        if (!res.ok) throw new Error(j.error || ("HTTP " + res.status));
        return j;
      });
    });
  }

  function refresh() {
    return fetch("/api/state").then(function (r) { return r.json(); }).then(paint);
  }

  function fileToB64(file) {
    return file.arrayBuffer().then(function (buf) {
      const bytes = new Uint8Array(buf);
      let bin = "";
      for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      return { name: file.name, b64: btoa(bin) };
    });
  }

  viewSimple.addEventListener("click", function () { setView(false); });
  viewAdvanced.addEventListener("click", function () { setView(true); });

  document.getElementById("btn-init").addEventListener("click", function () {
    post("/api/init", "{}").then(function (j) {
      kid.textContent = "New empty store. Drop a file you already have. We do not mail.";
      paint(j);
    }).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-drop").addEventListener("click", function () { dropFile.click(); });
  dropFile.addEventListener("change", function () {
    const f = dropFile.files && dropFile.files[0];
    if (!f) return;
    fileToB64(f).then(function (item) {
      return post("/api/drop", JSON.stringify({
        name: item.name,
        b64: item.b64,
        summary: document.getElementById("summary").value || "sample drop",
        source: document.getElementById("source").value || "",
        url: document.getElementById("url").value || ""
      }));
    }).then(paint).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-checkin").addEventListener("click", function () {
    post("/api/checkin", "{}").then(function (j) {
      kid.textContent = "Checked in. The clock reset. Tick will not copy while you are inside the window.";
      paint(j);
    }).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-arm").addEventListener("click", function () {
    const hours = parseInt(document.getElementById("hours").value, 10) || 1;
    post("/api/arm", JSON.stringify({ hours: hours })).then(function (j) {
      kid.textContent = "Armed for " + hours + " hour(s). Check in before then. Tick copies locally. We do not mail.";
      paint(j);
    }).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-tick").addEventListener("click", function () {
    post("/api/tick", "{}").then(function (j) {
      const last = j.last || {};
      if (last.released && last.reason !== "already released" && last.dest) {
        kid.textContent = "Overdue. Copied packet locally to released/. WhistleLock did not mail it.";
      } else if (last.reason === "inside window") {
        kid.textContent = "Inside the window. Nothing copied. Check in again before the hours run out.";
      } else if (last.reason === "already released") {
        kid.textContent = "Already released. Arm again if you want another local copy. We do not mail.";
      } else if (last.reason === "not armed") {
        kid.textContent = "Not armed. Tap Arm first.";
      } else {
        kid.textContent = JSON.stringify(last);
      }
      paint(j);
    }).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-verify").addEventListener("click", function () {
    post("/api/verify", "{}").then(paint).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-sample").addEventListener("click", function () {
    post("/api/sample", "{}").then(paint).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-list").addEventListener("click", function () {
    post("/api/list", "{}").then(function (j) {
      setView(true);
      paint(j);
    }).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-doctor").addEventListener("click", function () {
    post("/api/doctor", "{}").then(function (j) {
      kid.textContent = j.ok ? "Doctor passed. Engine, chain, dead-man, missing-file report, loopback. Does not mail." : "Doctor failed.";
      rowsPre.textContent = JSON.stringify(j, null, 2);
      setView(true);
    }).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-export").addEventListener("click", function () {
    post("/api/export", "{}").then(function (j) {
      const blob = new Blob([JSON.stringify(j.receipt, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = j.filename || "whistlelock-receipt.json";
      a.click();
      kid.textContent = "Exported a JSON receipt. Not a mailed packet.";
      paint(j.receipt);
    }).catch(function (e) { kid.textContent = String(e); });
  });
  document.getElementById("btn-packet").addEventListener("click", function () { packetFile.click(); });
  packetFile.addEventListener("change", function () {
    const f = packetFile.files && packetFile.files[0];
    if (!f) return;
    fileToB64(f).then(function (item) {
      return post("/api/packet", JSON.stringify(item));
    }).then(function (j) {
      kid.textContent = "Packet file placed locally. Tick copies it to released/ if you miss check-in. We do not mail it.";
      paint(j);
    }).catch(function (e) { kid.textContent = String(e); });
  });

  refresh().catch(function (e) { kid.textContent = String(e); });
})();
