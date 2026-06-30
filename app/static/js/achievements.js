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
