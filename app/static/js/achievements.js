// ════════════════════════════════════════════════════════════════
//  Achievement unlock celebrations on the hub.
//  Reads the freshly-earned achievements injected by the server and
//  shows a queued popup (golden particles + Web-Audio chime) for each.
//  The matching badge chip pulses with a NEW marker for a few seconds.
// ════════════════════════════════════════════════════════════════
(function () {
  var dataEl = document.getElementById("ach-new-data");
  var layer = document.getElementById("ach-popup-layer");
  if (!dataEl || !layer) return;

  var queue;
  try { queue = JSON.parse(dataEl.textContent) || []; } catch (e) { return; }

  // Stop the "newly-earned" pulse / NEW marker after a few seconds.
  setTimeout(function () {
    document.querySelectorAll(".badge-chip.newly-earned").forEach(function (c) {
      c.classList.remove("newly-earned");
    });
  }, 9000);

  if (!queue.length) return;

  function chime() {
    if (window.ATLAS_PREFS && window.ATLAS_PREFS.sound === false) return; // master sound off
    try {
      var C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      var a = new C();
      [523.25, 659.25, 783.99, 1046.5].forEach(function (f, i) {
        var o = a.createOscillator(), g = a.createGain();
        o.type = "sine"; o.frequency.value = f;
        var t = a.currentTime + i * 0.09;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.18, t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.5);
        o.connect(g); g.connect(a.destination);
        o.start(t); o.stop(t + 0.55);
      });
    } catch (e) {}
  }

  function showOne(ach, done) {
    var card = document.createElement("div");
    card.className = "ach-popup";
    var sparks = "";
    for (var i = 0; i < 16; i++) {
      var ang = (Math.PI * 2 / 16) * i, d = 70 + Math.random() * 36;
      sparks += '<span class="ach-spark" style="--dx:' + (Math.cos(ang) * d).toFixed(0) +
                'px;--dy:' + (Math.sin(ang) * d).toFixed(0) + 'px"></span>';
    }
    card.innerHTML =
      '<div class="ach-sparks">' + sparks + "</div>" +
      '<div class="ach-icon">' + (ach.icon || "🏆") + "</div>" +
      '<div class="ach-kicker">ACHIEVEMENT UNLOCKED</div>' +
      '<div class="ach-name"></div>' +
      '<div class="ach-desc"></div>';
    card.querySelector(".ach-name").textContent = ach.name || "";
    card.querySelector(".ach-desc").textContent = ach.desc || "";
    layer.appendChild(card);
    layer.classList.add("show");
    void card.offsetWidth;
    card.classList.add("in");
    chime();

    var closed = false;
    var timer = setTimeout(close, 3000);
    function close() {
      if (closed) return; closed = true;
      clearTimeout(timer);
      card.classList.remove("in"); card.classList.add("out");
      setTimeout(function () {
        if (card.parentNode) card.parentNode.removeChild(card);
        if (!layer.children.length) layer.classList.remove("show");
        done();
      }, 350);
    }
    card.addEventListener("click", close);
  }

  var idx = 0;
  function next() {
    if (idx >= queue.length) return;
    showOne(queue[idx++], function () { setTimeout(next, 250); });
  }
  setTimeout(next, 600); // let the hub settle first
})();

// ════════════════════════════════════════════════════════════════
//  On-demand badge detail card. Clicking (or Enter on) an EARNED badge
//  opens a small mini-modal with that level's score/attempts/date.
//  Read-only display; separate from the newly-earned celebration above.
// ════════════════════════════════════════════════════════════════
(function () {
  var layer = document.getElementById("badge-card-layer");
  var dataEl = document.getElementById("badge-detail-data");
  if (!layer || !dataEl) return;

  var detail;
  try { detail = JSON.parse(dataEl.textContent) || {}; } catch (e) { return; }

  var openFor = null; // the badge chip currently showing a card

  function row(label, value) {
    if (value === undefined || value === null || value === "") return null;
    var r = document.createElement("div");
    r.className = "bc-row";
    if (label) {
      var l = document.createElement("span"); l.className = "bc-label"; l.textContent = label;
      r.appendChild(l);
    } else {
      r.classList.add("bc-note");
    }
    var v = document.createElement("span"); v.className = "bc-value"; v.textContent = value;
    r.appendChild(v);
    return r;
  }

  function buildRows(d) {
    var rows = [];
    if (d.kind === "location") {
      rows.push(row("Location", d.location));
      rows.push(row("Score", d.score + " / " + d.max));
      rows.push(row("Attempts", d.attempts));
    } else if (d.kind === "atlas_sage") {
      rows.push(row("Score", d.score + " / " + d.max));
      if (d.rank) rows.push(row("Rank reached", d.rank));
    }
    return rows.filter(Boolean);
  }

  function close() {
    if (!openFor) return;
    layer.classList.remove("open");
    layer.hidden = true;
    layer.innerHTML = "";
    var chip = openFor; openFor = null;
    document.removeEventListener("keydown", onKey);
    if (chip && chip.focus) chip.focus();
  }
  function onKey(e) { if (e.key === "Escape") close(); }

  function open(chip) {
    var key = chip.getAttribute("data-badge-key");
    var d = detail[key];
    if (!d) return;
    if (openFor) close();
    openFor = chip;

    var card = document.createElement("div");
    card.className = "badge-card" + (d.perfect ? " is-perfect" : "");
    card.setAttribute("role", "dialog");
    card.setAttribute("aria-modal", "true");

    var closeBtn = document.createElement("button");
    closeBtn.className = "badge-card-close"; closeBtn.type = "button";
    closeBtn.setAttribute("aria-label", "Close"); closeBtn.innerHTML = "&times;";
    closeBtn.addEventListener("click", close);
    card.appendChild(closeBtn);

    var icon = document.createElement("div"); icon.className = "badge-card-icon"; icon.textContent = d.icon || "🏆";
    var title = document.createElement("div"); title.className = "badge-card-title"; title.textContent = d.name || "";
    card.appendChild(icon); card.appendChild(title);
    if (d.perfect) {
      var tag = document.createElement("div"); tag.className = "badge-card-perfect"; tag.textContent = "PERFECT";
      card.appendChild(tag);
    }

    var detailBox = document.createElement("div"); detailBox.className = "badge-card-detail";
    buildRows(d).forEach(function (r) { detailBox.appendChild(r); });
    card.appendChild(detailBox);

    if (d.desc) {
      var desc = document.createElement("p"); desc.className = "badge-card-desc"; desc.textContent = d.desc;
      card.appendChild(desc);
    }

    layer.innerHTML = "";
    layer.appendChild(card);
    layer.hidden = false;
    void layer.offsetWidth;
    layer.classList.add("open");
    document.addEventListener("keydown", onKey);
    closeBtn.focus();
  }

  // Close when clicking the dim backdrop (outside the card).
  layer.addEventListener("click", function (e) { if (e.target === layer) close(); });

  // Wire every earned badge (locked chips have no data-badge-key → inert).
  document.querySelectorAll(".badge-chip.earned[data-badge-key]").forEach(function (chip) {
    chip.addEventListener("click", function () { open(chip); });
    chip.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(chip); }
    });
  });
})();
