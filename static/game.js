const root = document.getElementById("root");

function html(s) {
  const d = document.createElement("div");
  d.innerHTML = s;
  return d.firstElementChild;
}

// --- sprite config ---
const FRAME_W = 16;
const FRAME_H = 24;
const SCALE   = 4;
const KNIGHT_W = FRAME_W * SCALE;
const KNIGHT_H = FRAME_H * SCALE;

const ANIM_FRAMES = {
  idle:   4,
  run:    4,
  jump:   6,
  hurt:   4,
  die:    4,
  attack: 5,
};

const ANIM_SRCS = {
  idle:   "sprites/idle.png",
  run:    "sprites/run.png",
  jump:   "sprites/jump.png",
  hurt:   "sprites/hurt.png",
  die:    "sprites/die.png",
  attack: "sprites/press.png",
};

const FRAME_RATES = {
  idle: 0.18, run: 0.09, jump: 0.1,
  hurt: 0.1,  die: 0.2,  attack: 0.06,
};

async function loadSheets() {
  const sheets = {};
  await Promise.all(
    Object.entries(ANIM_SRCS).map(([name, src]) =>
      new Promise((resolve) => {
        const img = new Image();
        img.onload  = () => { sheets[name] = img; resolve(); };
        img.onerror = () => { console.warn("missing sprite:", src); resolve(); };
        img.src = src;
      })
    )
  );
  Object.entries(sheets).forEach(([name, img]) => {
    console.log(name, img.width, img.height);
  });
  return sheets;
}

function drawKnight(ctx, sheets, knight, cameraX) {
  const img = sheets[knight.anim] || sheets["idle"];
  if (!img) return;

  const frameCount = ANIM_FRAMES[knight.anim] || 4;
  const srcFW = img.width / frameCount;
  const srcFH = img.height;
  const frame  = knight.frame % frameCount;
  const drawX  = Math.round(knight.x - cameraX);

  ctx.imageSmoothingEnabled = false;

  if (knight.hitTimer > 0 && Math.floor(knight.hitTimer * 20) % 2 === 0) {
    ctx.globalAlpha = 0.3;
  }

  ctx.save();
  if (knight.facing === -1) {
    ctx.translate(drawX + KNIGHT_W, knight.y);
    ctx.scale(-1, 1);
    ctx.drawImage(img, frame * srcFW, 0, srcFW, srcFH, 0, 0, KNIGHT_W, KNIGHT_H);
  } else {
    ctx.drawImage(img, frame * srcFW, 0, srcFW, srcFH, drawX, knight.y, KNIGHT_W, KNIGHT_H);
  }
  ctx.restore();
  ctx.globalAlpha = 1;
}

async function claim() {
  root.appendChild(html(`<p class="center">Waking up the knight...</p>`));
  let ok = false;
  try {
    const r = await fetch("/api/public/go_outside", { method: "POST" });
    const j = await r.json();
    ok = j.ok;
    if (!ok) {
      root.innerHTML = `<div class="center">
        <h2>🛡️ Knight is busy</h2>
        <p>Someone else has him outside. Try again shortly.</p>
        <a class="btn" href="/">← back</a>
      </div>`;
      return;
    }
  } catch {
    ok = true;
  }
  root.innerHTML = "";
  const sheets = await loadSheets();
  startGame(sheets);
}

function startGame(sheets) {
  const wrap = html(`
    <div style="position:relative;">
      <canvas id="cv" width="960" height="540"></canvas>
      <div id="hud" style="position:absolute;top:10px;left:12px;right:12px;
        display:flex;justify-content:space-between;align-items:center;
        color:#9bbc0f;font-family:monospace;font-size:20px;pointer-events:none;
        text-shadow:1px 1px 2px black;"></div>
      <button id="home" class="btn" style="position:absolute;top:10px;right:12px;
        background:#557a55;color:white;border:2px solid #9bbc0f;
        padding:6px 14px;cursor:pointer;font-family:monospace;font-size:14px;">
        GO HOME
      </button>
    </div>
  `);
  root.appendChild(wrap);

  const canvas = document.getElementById("cv");
  const ctx    = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const GROUND_Y = H - 80;

  const keys = new Set();
  window.addEventListener("keydown", e => {
    keys.add(e.key);
    if (["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"," "].includes(e.key))
      e.preventDefault();
  });
  window.addEventListener("keyup", e => keys.delete(e.key));
  const down = (...k) => k.some(x => keys.has(x));

  const knight = {
    x: 100, y: GROUND_Y - KNIGHT_H,
    vx: 0,  vy: 0,
    onGround: true,
    facing: 1,
    attackTimer: 0,
    hitTimer: 0,
    hp: 3,
    anim: "idle",
    frame: 0,
    frameTimer: 0,
  };

  const monsters = [], foods = [];
  let cameraX = 0, spawnT = 0, foodT = 0;
  let foodCount = 0, lastT = performance.now(), ending = false;

  const MONSTERS = ["👹","🦇","🕷️","👻","🧟"];
  const FOODS    = ["🍗","🍎","🧀","🍞","🍖"];
  const pick = a => a[Math.floor(Math.random() * a.length)];

  async function endRun() {
    if (ending) return;
    ending = true;
    const btn = document.getElementById("home");
    if (btn) { btn.disabled = true; btn.textContent = "going home..."; }
    try {
      await fetch("/api/public/return", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ food_collected: foodCount }),
      });
    } catch {}
    location.href = "/";
  }
  document.getElementById("home").onclick = endRun;

  function drawEmoji(emoji, wx, wy, size = 40) {
    ctx.font = `${size}px serif`;
    ctx.textBaseline = "top";
    ctx.fillText(emoji, Math.round(wx - cameraX), Math.round(wy));
  }

  function tick(now) {
    const dt = Math.min(0.05, (now - lastT) / 1000);
    lastT = now;

    let moving = false;
    if (down("ArrowLeft", "a")) {
      knight.vx = -220; knight.facing = -1; moving = true;
    } else if (down("ArrowRight", "d")) {
      knight.vx =  220; knight.facing =  1; moving = true;
    } else {
      knight.vx = 0;
    }

    if (down("ArrowUp", "w", " ") && knight.onGround) {
      knight.vy = -560;
      knight.onGround = false;
    }

    if (down("x", "X") && knight.attackTimer <= 0 && knight.hp > 0) {
      knight.attackTimer = 0.25;
    }

    knight.vy += 1500 * dt;
    knight.x  += knight.vx * dt;
    knight.y  += knight.vy * dt;

    if (knight.y + KNIGHT_H >= GROUND_Y) {
      knight.y = GROUND_Y - KNIGHT_H;
      knight.vy = 0;
      knight.onGround = true;
    }
    if (knight.x < 0) knight.x = 0;

    if (knight.attackTimer > 0) knight.attackTimer -= dt;
    if (knight.hitTimer > 0)    knight.hitTimer    -= dt;

    const prevAnim = knight.anim;
    if (knight.hp <= 0)              knight.anim = "die";
    else if (knight.hitTimer > 0)    knight.anim = "hurt";
    else if (knight.attackTimer > 0) knight.anim = "attack";
    else if (!knight.onGround)       knight.anim = "jump";
    else if (moving)                 knight.anim = "run";
    else                             knight.anim = "idle";

    if (knight.anim !== prevAnim) {
      knight.frame = 0;
      knight.frameTimer = 0;
    }

    knight.frameTimer += dt;
    const rate = FRAME_RATES[knight.anim] || 0.15;
    if (knight.frameTimer >= rate) {
      knight.frameTimer = 0;
      const frameCount = ANIM_FRAMES[knight.anim] || 4;
      knight.frame = (knight.frame + 1) % frameCount;
    }

    cameraX = Math.max(0, knight.x - W / 3);

    spawnT -= dt;
    if (spawnT <= 0) {
      spawnT = 1.6 + Math.random() * 1.4;
      monsters.push({
        x: cameraX + W + 60,
        y: GROUND_Y - 48,
        vx: -(1.2 + Math.random() * 0.8),
        emoji: pick(MONSTERS),
        alive: true,
      });
    }

    foodT -= dt;
    if (foodT <= 0) {
      foodT = 2.2 + Math.random() * 1.8;
      foods.push({
        x: cameraX + W + 40,
        y: GROUND_Y - 32,
        emoji: pick(FOODS),
        collected: false,
      });
    }

    for (const m of monsters) {
      if (!m.alive) continue;
      m.x += m.vx;

      if (knight.attackTimer > 0) {
        const reach = knight.facing === 1 ? KNIGHT_W + 24 : -24;
        const sx = knight.x + (knight.facing === 1 ? KNIGHT_W : 0);
        const ex = sx + reach;
        const lo = Math.min(sx, ex), hi = Math.max(sx, ex);
        if (m.x + 40 > lo && m.x < hi) m.alive = false;
      }

      if (
        m.alive && knight.hitTimer <= 0 && knight.hp > 0 &&
        m.x < knight.x + KNIGHT_W - 8 && m.x + 36 > knight.x + 8
      ) {
        knight.hp--;
        knight.hitTimer = 1;
        if (knight.hp <= 0) { endRun(); return; }
      }
    }
    for (let i = monsters.length - 1; i >= 0; i--)
      if (!monsters[i].alive || monsters[i].x < cameraX - 100)
        monsters.splice(i, 1);

    for (const f of foods) {
      if (f.collected) continue;
      if (
        f.x < knight.x + KNIGHT_W - 4 && f.x + 32 > knight.x + 4 &&
        f.y < knight.y + KNIGHT_H      && f.y + 32 > knight.y
      ) {
        f.collected = true;
        foodCount++;
      }
    }
    for (let i = foods.length - 1; i >= 0; i--)
      if (foods[i].collected || foods[i].x < cameraX - 100)
        foods.splice(i, 1);

    // render background
    const grd = ctx.createLinearGradient(0, 0, 0, H);
    grd.addColorStop(0, "#1a1a3a");
    grd.addColorStop(1, "#3a5a3a");
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = "rgba(255,255,255,0.6)";
    for (let i = 0; i < 30; i++) {
      const sx = ((i * 137 - cameraX * 0.2) % W + W) % W;
      const sy = (i * 53) % (GROUND_Y - 40);
      ctx.fillRect(sx, sy, 2, 2);
    }

    ctx.fillStyle = "#2a4a2a";
    for (let i = 0; i < 6; i++) {
      const bx = i * 260 - ((cameraX * 0.4) % 260);
      ctx.beginPath();
      ctx.moveTo(bx, GROUND_Y);
      ctx.lineTo(bx + 130, GROUND_Y - 140);
      ctx.lineTo(bx + 260, GROUND_Y);
      ctx.closePath();
      ctx.fill();
    }

    ctx.fillStyle = "#5a3a1a"; ctx.fillRect(0, GROUND_Y, W, H - GROUND_Y);
    ctx.fillStyle = "#7a5a2a"; ctx.fillRect(0, GROUND_Y, W, 6);

    for (const f of foods)    if (!f.collected) drawEmoji(f.emoji, f.x, f.y, 32);
    for (const m of monsters) if (m.alive)      drawEmoji(m.emoji, m.x, m.y, 44);

    drawKnight(ctx, sheets, knight, cameraX);

    // HUD
    const hud = document.getElementById("hud");
    if (hud) {
      const hearts = "❤️".repeat(Math.max(0, knight.hp)) + "🖤".repeat(Math.max(0, 3 - knight.hp));
      hud.innerHTML = `<span style="font-size:24px">${hearts}</span><span>🍖 ${foodCount}</span>`;
    }

    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

claim();