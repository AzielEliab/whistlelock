/* WhistleLock local UI. No CDN. No telemetry. */
(function () {
  var kid = document.getElementById("kid-plain");
  var verifyLine = document.getElementById("verify-line");
  var deadmanLine = document.getElementById("deadman-line");
  var rowsPre = document.getElementById("rows-pre");
  var dropFile = document.getElementById("drop-file");
  var packetFile = document.getElementById("packet-file");

  function showAdvanced() {
    var adv = document.getElementById("advanced");
    if (adv) adv.open = true;
  }

  function fail(err) {
    var reason = err && err.message ? err.message : String(err);
    kid.classList.add("bad");
    kid.textContent = reason + " Next: reload this page, or run whistlelock doctor in a terminal.";
  }

  function paint(state) {
    var counts = (state && state.counts) || {};
    var drops = counts.drops || 0;
    var dm = (state && state.deadman) || {};
    var verify = (state && state.verify) || {};
    var ok = verify.ok === true;
    kid.classList.toggle("bad", verify.ok === false);
    var status;
    if (verify.ok === true) {
      status = drops === 1
        ? "Chain checks out. 1 drop on this computer."
        : "Chain checks out. " + drops + " drops on this computer.";
    } else if (verify.ok === false) {
      status = "The chain needs a look. " + ((verify.errors && verify.errors[0]) || (verify.missing_files && verify.missing_files[0]) || "Verify failed.");
    } else {
      status = "Drop a file you already have.";
    }
    if (!dm.armed) {
      status += " Check-in clock is not armed.";
    } else if (dm.released) {
      status += " A local copy was already made.";
    } else {
      var hours = dm.interval_hours || 0;
      status += " Armed for " + hours + " hour" + (hours === 1 ? "" : "s") + ".";
    }
    kid.textContent = status;
    if (verify.ok === undefined) {
      verifyLine.textContent = "";
    } else if (ok) {
      verifyLine.textContent = "Chain checks out. Rows: " + verify.rows + ".";
    } else {
      verifyLine.textContent = "Needs a look. Rows: " + verify.rows + ".";
    }
    deadmanLine.textContent = dm.armed
      ? "Armed for " + (dm.interval_hours || 0) + " hour(s). Last check-in: " + (dm.last_checkin || "none") + "."
      : "Check-in clock is not armed.";
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
        if (!res.ok) throw new Error(j.error || ("Request failed (" + res.status + ")."));
        return j;
      });
    });
  }

  function refresh() {
    return fetch("/api/state").then(function (r) { return r.json(); }).then(paint);
  }

  function fileToB64(file) {
    return file.arrayBuffer().then(function (buf) {
      var bytes = new Uint8Array(buf);
      var bin = "";
      for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      return { name: file.name, b64: btoa(bin) };
    });
  }

  function value(id) {
    var el = document.getElementById(id);
    return el ? el.value : "";
  }

  document.getElementById("btn-init").addEventListener("click", function () {
    post("/api/init", "{}").then(function (j) {
      paint(j);
      kid.classList.remove("bad");
      kid.textContent = "New store on this computer. Drop a file you already have.";
    }).catch(fail);
  });

  document.getElementById("btn-drop").addEventListener("click", function () { dropFile.click(); });
  dropFile.addEventListener("change", function () {
    var file = dropFile.files && dropFile.files[0];
    if (!file) return;
    fileToB64(file).then(function (item) {
      return post("/api/drop", JSON.stringify({
        name: item.name,
        b64: item.b64,
        summary: value("summary") || "sample drop",
        source: value("source"),
        url: value("url")
      }));
    }).then(function (j) {
      paint(j);
      kid.classList.remove("bad");
      kid.textContent = "Dropped " + file.name + ". It is stored on this computer.";
    }).catch(fail);
  });

  document.getElementById("btn-checkin").addEventListener("click", function () {
    post("/api/checkin", "{}").then(function (j) {
      paint(j);
      kid.classList.remove("bad");
      kid.textContent = "Checked in. The clock reset.";
    }).catch(fail);
  });

  document.getElementById("btn-arm").addEventListener("click", function () {
    showAdvanced();
    var hours = parseInt(value("hours"), 10) || 1;
    post("/api/arm", JSON.stringify({ hours: hours })).then(function (j) {
      paint(j);
      kid.classList.remove("bad");
      kid.textContent = "Armed for " + hours + " hour" + (hours === 1 ? "" : "s") + ". Check in before then.";
    }).catch(fail);
  });

  document.getElementById("btn-tick").addEventListener("click", function () {
    showAdvanced();
    post("/api/tick", "{}").then(function (j) {
      paint(j);
      var last = j.last || {};
      kid.classList.remove("bad");
      if (last.released && last.reason !== "already released" && last.dest) {
        kid.textContent = "Copied the packet on this computer. It was not mailed.";
      } else if (last.reason === "inside window") {
        kid.textContent = "Inside the window. Nothing was copied.";
      } else if (last.reason === "already released") {
        kid.textContent = "Already copied. Arm again if you want another local copy.";
      } else if (last.reason === "not armed") {
        kid.textContent = "Not armed yet. Set the hours, then tap Arm.";
      } else {
        kid.textContent = "Tick finished. Tap List to read the detail.";
      }
    }).catch(fail);
  });

  document.getElementById("btn-verify").addEventListener("click", function () {
    post("/api/verify", "{}").then(paint).catch(fail);
  });

  document.getElementById("btn-sample").addEventListener("click", function () {
    showAdvanced();
    post("/api/sample", "{}").then(function (j) {
      paint(j);
      kid.classList.remove("bad");
      kid.textContent = "Sample store is ready. The demo drop is named sample drop.";
    }).catch(fail);
  });

  document.getElementById("btn-list").addEventListener("click", function () {
    showAdvanced();
    post("/api/list", "{}").then(paint).catch(fail);
  });

  document.getElementById("btn-doctor").addEventListener("click", function () {
    showAdvanced();
    post("/api/doctor", "{}").then(function (j) {
      kid.classList.toggle("bad", !j.ok);
      kid.textContent = j.ok
        ? "Doctor passed."
        : "Doctor failed. The ledger below shows which check failed.";
      rowsPre.textContent = JSON.stringify(j, null, 2);
    }).catch(fail);
  });

  document.getElementById("btn-export").addEventListener("click", function () {
    showAdvanced();
    post("/api/export", "{}").then(function (j) {
      var blob = new Blob([JSON.stringify(j.receipt, null, 2)], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = j.filename || "whistlelock-receipt.json";
      a.click();
      paint(j.receipt);
      kid.classList.remove("bad");
      kid.textContent = "Saved a JSON receipt on this computer.";
    }).catch(fail);
  });

  document.getElementById("btn-packet").addEventListener("click", function () { packetFile.click(); });
  packetFile.addEventListener("change", function () {
    var file = packetFile.files && packetFile.files[0];
    if (!file) return;
    showAdvanced();
    fileToB64(file).then(function (item) {
      return post("/api/packet", JSON.stringify(item));
    }).then(function (j) {
      paint(j);
      kid.classList.remove("bad");
      kid.textContent = "Packet file placed on this computer. Tick copies it if a check-in is missed.";
    }).catch(fail);
  });

  refresh().catch(fail);
})();
