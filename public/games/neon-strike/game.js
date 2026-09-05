(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const canvas = $("#game-canvas");
  const ctx = canvas.getContext("2d", { alpha: false });
  const minimap = $("#minimap");
  const mctx = minimap.getContext("2d");

  const TAU = Math.PI * 2;
  const FOV = Math.PI / 3;
  const MAP_SIZE = 24;
  const RAY_STEP = 2;
  const isTouch = matchMedia("(pointer: coarse)").matches;

  const heroes = [
    { id: "vanguard", name: "先锋·洛克", role: "均衡突击", note: "厚重护甲，适合第一次出击", hp: 120, shield: 45, speed: 3.2, color: "#25e7ff", mark: "V", stat: 4 },
    { id: "scout", name: "疾影·米娅", role: "高速侦察", note: "移动最快，冲刺恢复更迅速", hp: 88, shield: 30, speed: 4.25, color: "#b8ff59", mark: "S", stat: 5 },
    { id: "engineer", name: "机巧·阿拓", role: "护盾工程", note: "能量护盾更强，近战火力凶猛", hp: 100, shield: 78, speed: 3.05, color: "#ff9d3b", mark: "E", stat: 4 },
    { id: "sentinel", name: "星卫·诺亚", role: "精准射手", note: "远距离伤害高，弹药管理关键", hp: 102, shield: 42, speed: 3.45, color: "#a77bff", mark: "N", stat: 5 }
  ];

  const maps = [
    {
      id: "harbor", name: "霓虹港", note: "开阔中庭 · 快速交火", color: "#25e7ff",
      sky: ["#06152c", "#173969"], floor: ["#07111d", "#102536"], walls: ["#0d5c72", "#12839a", "#25e7ff"], seed: 11,
      blocks: [[5,2,1,7,1],[9,5,5,1,2],[17,2,1,7,1],[3,12,6,1,2],[12,10,1,7,1],[16,13,5,1,2],[6,17,1,4,1],[16,17,1,4,1],[9,20,6,1,2]]
    },
    {
      id: "mars", name: "赤砂基地", note: "窄道掩体 · 近距突袭", color: "#ff7849",
      sky: ["#210a12", "#8c3429"], floor: ["#1a0b0a", "#4a2018"], walls: ["#7e2d24", "#b44a34", "#ff9d57"], seed: 23,
      blocks: [[4,3,4,2,1],[11,2,2,6,2],[17,3,3,4,1],[3,10,6,2,2],[14,9,7,2,1],[7,15,2,6,1],[12,14,5,2,2],[19,14,2,7,1],[11,19,5,2,1]]
    },
    {
      id: "ice", name: "极光冰站", note: "长廊交错 · 精准射击", color: "#76a8ff",
      sky: ["#08122b", "#305b96"], floor: ["#091426", "#1c3954"], walls: ["#255582", "#4688b8", "#a6f2ff"], seed: 37,
      blocks: [[5,2,1,8,1],[10,2,1,5,2],[15,2,1,8,1],[20,4,1,6,2],[3,12,6,1,2],[11,10,1,8,1],[14,13,7,1,2],[5,16,1,6,1],[15,17,1,5,1],[18,19,4,1,2]]
    },
    {
      id: "sky", name: "云端要塞", note: "环形路线 · 多向包围", color: "#bd78ff",
      sky: ["#100a2b", "#43308a"], floor: ["#0d0c20", "#222040"], walls: ["#513a8f", "#7454b7", "#d095ff"], seed: 51,
      blocks: [[4,4,5,1,1],[4,5,1,4,1],[15,4,5,1,1],[19,5,1,4,1],[8,9,8,1,2],[3,13,5,1,2],[16,13,5,1,2],[8,14,1,6,1],[15,14,1,6,1],[10,18,4,2,2]]
    }
  ];

  const weaponFamilies = [
    { id: "pulse", name: "脉冲步枪", short: "PR", mag: 30, reserve: 180, damage: 24, cooldown: 118, reload: 1250, spread: .018, pellets: 1, range: 15, color: "#25e7ff", kick: 7, form: 0, pitch: 170 },
    { id: "scatter", name: "星火霰射器", short: "SG", mag: 8, reserve: 48, damage: 13, cooldown: 620, reload: 1450, spread: .11, pellets: 7, range: 8, color: "#ff9d3b", kick: 16, form: 1, pitch: 105 },
    { id: "ion", name: "离子连发器", short: "IX", mag: 42, reserve: 210, damage: 15, cooldown: 82, reload: 1100, spread: .035, pellets: 1, range: 12, color: "#b8ff59", kick: 5, form: 3, pitch: 250 },
    { id: "rail", name: "极光轨道枪", short: "RG", mag: 6, reserve: 36, damage: 82, cooldown: 820, reload: 1650, spread: .005, pellets: 1, range: 22, color: "#b584ff", kick: 22, form: 2, pitch: 78 },
    { id: "burst", name: "棱镜三连枪", short: "BX", mag: 27, reserve: 162, damage: 18, cooldown: 155, reload: 1180, spread: .022, pellets: 3, range: 14, color: "#ff6fd8", kick: 9, form: 0, pitch: 205 },
    { id: "beam", name: "日冕光束器", short: "CB", mag: 55, reserve: 275, damage: 11, cooldown: 68, reload: 1380, spread: .012, pellets: 1, range: 17, color: "#ffe45f", kick: 4, form: 3, pitch: 310 },
    { id: "comet", name: "彗星爆能炮", short: "CX", mag: 5, reserve: 30, damage: 108, cooldown: 980, reload: 1780, spread: .025, pellets: 1, range: 13, color: "#ff5d5d", kick: 26, form: 1, pitch: 62 },
    { id: "cryo", name: "寒潮卡宾枪", short: "FC", mag: 24, reserve: 144, damage: 29, cooldown: 145, reload: 1210, spread: .014, pellets: 1, range: 16, color: "#72b9ff", kick: 8, form: 0, pitch: 190 },
    { id: "arc", name: "雷弧发射器", short: "AL", mag: 14, reserve: 84, damage: 31, cooldown: 280, reload: 1320, spread: .065, pellets: 2, range: 10, color: "#70ffbb", kick: 12, form: 2, pitch: 135 },
    { id: "photon", name: "光子手炮", short: "PH", mag: 12, reserve: 84, damage: 48, cooldown: 360, reload: 960, spread: .016, pellets: 1, range: 14, color: "#ff8fb3", kick: 14, form: 3, pitch: 118 }
  ];

  const weaponSeries = [
    { name: "零式", trait: "均衡核心", rarity: "标准", power: 1, speed: 1, mag: 0, precision: 1 },
    { name: "曙光", trait: "快速装填", rarity: "标准", power: 1.02, speed: .98, mag: 1, precision: .98 },
    { name: "跃迁", trait: "增容弹仓", rarity: "标准", power: .98, speed: .97, mag: 4, precision: 1.02 },
    { name: "幻影", trait: "低散布", rarity: "稀有", power: 1.04, speed: .96, mag: 2, precision: .88 },
    { name: "烈星", trait: "高能弹头", rarity: "稀有", power: 1.12, speed: 1.06, mag: 0, precision: 1.02 },
    { name: "天穹", trait: "远程聚焦", rarity: "稀有", power: 1.08, speed: .94, mag: 2, precision: .86 },
    { name: "深空", trait: "稳定循环", rarity: "史诗", power: 1.1, speed: .9, mag: 5, precision: .9 },
    { name: "超新星", trait: "爆发增幅", rarity: "史诗", power: 1.2, speed: 1.04, mag: 1, precision: .96 },
    { name: "奇点", trait: "贯穿聚能", rarity: "史诗", power: 1.23, speed: 1.08, mag: 0, precision: .78 },
    { name: "量子", trait: "极速循环", rarity: "传说", power: 1.16, speed: .82, mag: 6, precision: .84 },
    { name: "永昼", trait: "全域强化", rarity: "传说", power: 1.28, speed: .86, mag: 4, precision: .76 },
    { name: "神谕", trait: "终极校准", rarity: "传说", power: 1.36, speed: .9, mag: 3, precision: .7 }
  ];

  const rarityColors = { "标准": "#94a6c4", "稀有": "#25e7ff", "史诗": "#b584ff", "传说": "#ffca55" };

  const weapons = weaponFamilies.flatMap((family, familyIndex) => weaponSeries.map((series, seriesIndex) => ({
    id: `${family.id}-${seriesIndex + 1}`,
    family: family.id,
    familyName: family.name,
    name: `${series.name}·${family.name}`,
    code: `${family.short}-${String(seriesIndex + 1).padStart(2, "0")}`,
    short: family.short,
    trait: series.trait,
    rarity: series.rarity,
    mag: Math.max(3, family.mag + series.mag + (seriesIndex % 3 === 2 ? 1 : 0)),
    reserve: Math.round((family.reserve + series.mag * 5) * (1 + seriesIndex * .018)),
    damage: Math.round(family.damage * series.power * (1 + familyIndex * .003)),
    cooldown: Math.max(52, Math.round(family.cooldown * series.speed)),
    reload: Math.max(720, Math.round(family.reload * (1 - seriesIndex * .012))),
    spread: Math.max(.003, family.spread * series.precision),
    pellets: family.pellets,
    range: Number((family.range + seriesIndex * .28).toFixed(1)),
    color: family.color,
    kick: Math.round(family.kick * (1 + seriesIndex * .018)),
    form: family.form,
    pitch: family.pitch + seriesIndex * 5
  })));

  const enemyKinds = {
    scout: { name: "侦察机", hp: 42, speed: 1.25, damage: 6, range: 6.5, cooldown: 1200, size: 0.72, color: "#54efff", score: 100 },
    raider: { name: "突击机器人", hp: 72, speed: 0.88, damage: 9, range: 7.8, cooldown: 1500, size: 0.9, color: "#ff5e83", score: 160 },
    heavy: { name: "重装卫士", hp: 155, speed: 0.5, damage: 16, range: 7.2, cooldown: 2050, size: 1.2, color: "#ffad45", score: 320 },
    drone: { name: "悬浮蜂群", hp: 55, speed: 1.55, damage: 5, range: 6, cooldown: 950, size: 0.64, color: "#b9ff59", score: 140 },
    elite: { name: "虚空队长", hp: 240, speed: 0.72, damage: 18, range: 9, cooldown: 1350, size: 1.3, color: "#ae75ff", score: 650 }
  };

  const state = {
    mode: "menu",
    selectedHero: 0,
    selectedMap: 0,
    loadout: [0, 16, 44],
    selectedSlot: 0,
    armoryFamily: "all",
    armorySearch: "",
    map: [],
    player: null,
    enemies: [],
    pickups: [],
    projectiles: [],
    particles: [],
    keys: {},
    firing: false,
    wave: 1,
    score: 0,
    combo: 1,
    comboTimer: 0,
    shots: 0,
    hits: 0,
    lastShot: 0,
    lastTime: 0,
    recoil: 0,
    shake: 0,
    muzzle: 0,
    wavePending: false,
    sound: true,
    audio: null,
    dashCooldown: 0,
    reloading: false,
    reloadEnds: 0,
    announcementTimer: 0,
    mobileMove: { x: 0, y: 0 },
    touchAimX: null,
    renderedEnemies: []
  };

  let zBuffer = new Float32Array(1);
  const spriteTextures = {};

  function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
  function normAngle(value) {
    while (value < -Math.PI) value += TAU;
    while (value > Math.PI) value -= TAU;
    return value;
  }
  function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
  function seeded(seed) {
    let x = Math.sin(seed * 9283.17) * 43758.5453;
    return x - Math.floor(x);
  }

  function makeMap(definition) {
    const grid = Array.from({ length: MAP_SIZE }, (_, y) =>
      Array.from({ length: MAP_SIZE }, (_, x) => (x === 0 || y === 0 || x === MAP_SIZE - 1 || y === MAP_SIZE - 1 ? 1 : 0))
    );
    for (const [sx, sy, width, height, type] of definition.blocks) {
      for (let y = sy; y < Math.min(MAP_SIZE - 1, sy + height); y++) {
        for (let x = sx; x < Math.min(MAP_SIZE - 1, sx + width); x++) grid[y][x] = type;
      }
    }
    [[2,2],[3,2],[2,3],[21,21],[20,21],[21,20]].forEach(([x,y]) => { grid[y][x] = 0; });
    return grid;
  }

  function isWall(x, y) {
    const gx = Math.floor(x), gy = Math.floor(y);
    return gx < 0 || gy < 0 || gx >= MAP_SIZE || gy >= MAP_SIZE || state.map[gy][gx] > 0;
  }

  function canStand(x, y, radius = 0.24) {
    return !isWall(x - radius, y - radius) && !isWall(x + radius, y - radius) && !isWall(x - radius, y + radius) && !isWall(x + radius, y + radius);
  }

  function lineClear(ax, ay, bx, by) {
    const distance = Math.hypot(bx - ax, by - ay);
    const steps = Math.ceil(distance * 6);
    for (let i = 1; i < steps; i++) {
      const t = i / steps;
      if (isWall(ax + (bx - ax) * t, ay + (by - ay) * t)) return false;
    }
    return true;
  }

  function initUI() {
    const heroList = $("#hero-list");
    heroes.forEach((hero, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `hero-card${index === 0 ? " selected" : ""}`;
      button.innerHTML = `<strong>${hero.name}</strong><small>${hero.role} · ${hero.note}</small><span class="stat-dots">${[0,1,2,3,4].map(i => `<i class="${i < hero.stat ? "on" : ""}"></i>`).join("")}</span>`;
      button.addEventListener("click", () => selectHero(index));
      heroList.appendChild(button);
    });

    const mapList = $("#map-list");
    maps.forEach((map, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `map-card${index === 0 ? " selected" : ""}`;
      button.dataset.index = String(index + 1).padStart(2, "0");
      button.style.setProperty("--map-color", map.color);
      button.innerHTML = `<strong>${map.name}</strong><small>${map.note}</small>`;
      button.addEventListener("click", () => selectMap(index));
      mapList.appendChild(button);
    });

    const slots = $("#weapon-slots");
    for (let index = 0; index < 3; index++) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "weapon-slot";
      button.addEventListener("click", () => switchWeaponSlot(index));
      slots.appendChild(button);
    }

    loadSavedLoadout();
    buildFamilyFilters();
    renderLoadoutUI();
    renderArmory();

    $("#start-button").addEventListener("click", startGame);
    $("#open-armory-button").addEventListener("click", openArmory);
    $("#close-armory-button").addEventListener("click", closeArmory);
    $("#weapon-search-input").addEventListener("input", event => {
      state.armorySearch = event.target.value.trim().toLowerCase();
      renderArmory();
    });
    $("#pause-button").addEventListener("click", pauseGame);
    $("#resume-button").addEventListener("click", resumeGame);
    $("#restart-button").addEventListener("click", startGame);
    $("#retry-button").addEventListener("click", startGame);
    $("#menu-button").addEventListener("click", returnToMenu);
    $("#result-menu-button").addEventListener("click", returnToMenu);
    $("#sound-button").addEventListener("click", toggleSound);
    $("#fullscreen-button").addEventListener("click", toggleFullscreen);
    setupInput();
    resize();
    drawBackdrop();
  }

  function loadSavedLoadout() {
    try {
      const saved = JSON.parse(localStorage.getItem("neon-strike-loadout") || "null");
      if (Array.isArray(saved) && saved.length === 3 && new Set(saved).size === 3 && saved.every(id => Number.isInteger(id) && weapons[id])) state.loadout = saved;
    } catch {}
  }

  function saveLoadout() {
    try { localStorage.setItem("neon-strike-loadout", JSON.stringify(state.loadout)); } catch {}
  }

  function buildFamilyFilters() {
    const host = $("#family-filters");
    const options = [{ id: "all", name: "全部" }, ...weaponFamilies];
    options.forEach(option => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `family-filter${option.id === "all" ? " active" : ""}`;
      button.textContent = option.name;
      button.addEventListener("click", () => {
        state.armoryFamily = option.id;
        host.querySelectorAll(".family-filter").forEach(el => el.classList.toggle("active", el === button));
        renderArmory();
      });
      host.appendChild(button);
    });
  }

  function createLoadoutSlot(slotIndex, armoryMode) {
    const weaponId = state.loadout[slotIndex];
    const weapon = weapons[weaponId];
    const button = document.createElement("button");
    button.type = "button";
    button.className = `loadout-slot${state.selectedSlot === slotIndex ? " selected" : ""}`;
    button.dataset.slot = `槽位 ${slotIndex + 1}`;
    button.style.setProperty("--slot-color", weapon.color);
    button.innerHTML = `<strong>${weapon.name}</strong><small>${weapon.code} · ${weapon.trait}</small>`;
    button.addEventListener("click", () => {
      state.selectedSlot = slotIndex;
      renderLoadoutUI();
      renderArmory();
      if (!armoryMode) openArmory();
    });
    return button;
  }

  function renderLoadoutUI() {
    const menu = $("#menu-loadout");
    const armory = $("#armory-loadout");
    menu.innerHTML = "";
    armory.innerHTML = "";
    for (let slot = 0; slot < 3; slot++) {
      menu.appendChild(createLoadoutSlot(slot, false));
      armory.appendChild(createLoadoutSlot(slot, true));
    }
    document.querySelectorAll(".weapon-slot").forEach((button, slot) => {
      const weapon = weapons[state.loadout[slot]];
      button.textContent = `${slot + 1} ${weapon.short}`;
      button.setAttribute("aria-label", `切换到${weapon.name}`);
      button.style.setProperty("--slot-color", weapon.color);
    });
  }

  function renderArmory() {
    const host = $("#armory-grid");
    const query = state.armorySearch;
    const visible = weapons.filter(weapon => {
      const familyMatch = state.armoryFamily === "all" || weapon.family === state.armoryFamily;
      const queryMatch = !query || `${weapon.name} ${weapon.familyName} ${weapon.code} ${weapon.trait} ${weapon.rarity}`.toLowerCase().includes(query);
      return familyMatch && queryMatch;
    });
    $("#armory-count").textContent = `${visible.length} 种武器`;
    host.innerHTML = "";
    if (!visible.length) {
      host.innerHTML = '<p class="armory-empty">没有找到匹配武器，试试其他关键词。</p>';
      return;
    }
    const fragment = document.createDocumentFragment();
    visible.forEach(weapon => {
      const weaponId = weapons.indexOf(weapon);
      const equippedSlot = state.loadout.indexOf(weaponId);
      const button = document.createElement("button");
      button.type = "button";
      button.className = `weapon-card${equippedSlot >= 0 ? " equipped" : ""}`;
      button.style.setProperty("--weapon-color", weapon.color);
      button.style.setProperty("--rarity-color", rarityColors[weapon.rarity]);
      button.innerHTML = `<span class="weapon-top"><span class="weapon-code">${weapon.code}</span><span class="rarity">${weapon.rarity}</span></span><strong>${weapon.name}</strong><small>${weapon.trait}</small><span class="weapon-stats"><span class="weapon-stat">伤害 <b>${weapon.damage}</b></span><span class="weapon-stat">弹匣 <b>${weapon.mag}</b></span><span class="weapon-stat">射速 <b>${Math.round(60000 / weapon.cooldown)}</b></span><span class="weapon-stat">射程 <b>${weapon.range}</b></span></span>${equippedSlot >= 0 ? `<span class="equipped-tag">已装备在槽位 ${equippedSlot + 1}</span>` : ""}`;
      button.addEventListener("click", () => equipWeapon(weaponId));
      fragment.appendChild(button);
    });
    host.appendChild(fragment);
  }

  function equipWeapon(weaponId) {
    const existingSlot = state.loadout.indexOf(weaponId);
    if (existingSlot >= 0) {
      state.selectedSlot = existingSlot;
    } else {
      state.loadout[state.selectedSlot] = weaponId;
      saveLoadout();
      tone(390 + state.selectedSlot * 75, 0.06, "triangle", 0.035);
    }
    renderLoadoutUI();
    renderArmory();
  }

  function openArmory() {
    if (state.mode !== "menu") return;
    $("#armory-screen").classList.add("active");
    renderLoadoutUI();
    renderArmory();
  }

  function closeArmory() {
    $("#armory-screen").classList.remove("active");
  }

  function selectHero(index) {
    state.selectedHero = index;
    document.querySelectorAll(".hero-card").forEach((el, i) => el.classList.toggle("selected", i === index));
    tone(420 + index * 80, 0.05, "sine", 0.04);
  }

  function selectMap(index) {
    state.selectedMap = index;
    document.querySelectorAll(".map-card").forEach((el, i) => el.classList.toggle("selected", i === index));
    tone(280 + index * 55, 0.06, "triangle", 0.035);
  }

  function startGame() {
    const hero = heroes[state.selectedHero];
    const map = maps[state.selectedMap];
    state.map = makeMap(map);
    state.player = {
      x: 2.5, y: 2.5, angle: 0.2,
      hp: hero.hp, maxHp: hero.hp,
      shield: hero.shield, maxShield: hero.shield,
      speed: hero.speed,
      weapon: state.loadout[0],
      weaponSlot: 0,
      ammo: weapons.map(w => w.mag),
      reserve: weapons.map(w => w.reserve),
      shieldDelay: 0
    };
    Object.assign(state, {
      enemies: [], pickups: [], projectiles: [], particles: [],
      wave: 1, score: 0, combo: 1, comboTimer: 0, shots: 0, hits: 0,
      lastShot: 0, recoil: 0, shake: 0, muzzle: 0, wavePending: false,
      dashCooldown: 0, reloading: false, announcementTimer: 0,
      mode: "playing"
    });
    $("#start-screen").classList.remove("active");
    $("#armory-screen").classList.remove("active");
    $("#pause-screen").classList.remove("active");
    $("#result-screen").classList.remove("active");
    $("#hud").classList.add("active");
    $("#touch-controls").classList.toggle("active", isTouch);
    spawnWave();
    updateHUD();
    showAnnouncement(`${map.name} // 第 1 波`);
    state.lastTime = performance.now();
    initAudio();
    if (!isTouch) canvas.requestPointerLock?.();
  }

  function returnToMenu() {
    state.mode = "menu";
    document.exitPointerLock?.();
    $("#hud").classList.remove("active");
    $("#touch-controls").classList.remove("active");
    $("#pause-screen").classList.remove("active");
    $("#result-screen").classList.remove("active");
    $("#armory-screen").classList.remove("active");
    $("#start-screen").classList.add("active");
    drawBackdrop();
  }

  function pauseGame() {
    if (state.mode !== "playing") return;
    state.mode = "paused";
    state.firing = false;
    document.exitPointerLock?.();
    $("#pause-screen").classList.add("active");
  }

  function resumeGame() {
    if (state.mode !== "paused") return;
    state.mode = "playing";
    state.lastTime = performance.now();
    $("#pause-screen").classList.remove("active");
    if (!isTouch) canvas.requestPointerLock?.();
  }

  function endGame() {
    state.mode = "ended";
    state.firing = false;
    document.exitPointerLock?.();
    $("#result-score").textContent = state.score.toLocaleString("zh-CN");
    $("#result-wave").textContent = state.wave;
    $("#result-accuracy").textContent = `${state.shots ? Math.round(state.hits / state.shots * 100) : 0}%`;
    $("#result-screen").classList.add("active");
    $("#touch-controls").classList.remove("active");
    tone(110, 0.35, "sawtooth", 0.055);
  }

  function setupInput() {
    addEventListener("keydown", event => {
      state.keys[event.code] = true;
      if (["Digit1","Digit2","Digit3"].includes(event.code)) switchWeaponSlot(Number(event.code.slice(-1)) - 1);
      if (event.code === "KeyR") reload();
      if (event.code === "Escape" && state.mode === "playing") pauseGame();
      if (event.code === "Escape" && state.mode === "menu") closeArmory();
      if (event.code === "KeyP") state.mode === "playing" ? pauseGame() : resumeGame();
      if (event.code === "ShiftLeft" || event.code === "ShiftRight") dash();
    });
    addEventListener("keyup", event => { state.keys[event.code] = false; });
    addEventListener("mousemove", event => {
      if (state.mode === "playing" && document.pointerLockElement === canvas) state.player.angle += event.movementX * 0.00235;
    });
    canvas.addEventListener("mousedown", event => {
      if (state.mode !== "playing") return;
      if (!isTouch && document.pointerLockElement !== canvas) { canvas.requestPointerLock?.(); return; }
      if (event.button === 0) state.firing = true;
    });
    addEventListener("mouseup", () => { state.firing = false; });
    canvas.addEventListener("contextmenu", event => event.preventDefault());
    canvas.addEventListener("wheel", event => {
      if (state.mode !== "playing") return;
      event.preventDefault();
      switchWeaponSlot((state.player.weaponSlot + (event.deltaY > 0 ? 1 : 2)) % 3);
    }, { passive: false });
    addEventListener("blur", () => { if (state.mode === "playing") pauseGame(); });
    addEventListener("resize", resize);
    document.addEventListener("fullscreenchange", () => $("#fullscreen-button").textContent = document.fullscreenElement ? "退出全屏" : "全屏");

    canvas.addEventListener("touchstart", event => {
      if (state.mode !== "playing") return;
      const touch = event.changedTouches[0];
      if (touch.clientX > innerWidth * 0.35) state.touchAimX = touch.clientX;
    }, { passive: true });
    canvas.addEventListener("touchmove", event => {
      if (state.mode !== "playing" || state.touchAimX === null) return;
      const touch = event.changedTouches[0];
      state.player.angle += (touch.clientX - state.touchAimX) * 0.006;
      state.touchAimX = touch.clientX;
    }, { passive: true });
    canvas.addEventListener("touchend", () => { state.touchAimX = null; }, { passive: true });

    const pad = $("#move-pad");
    const knob = pad.querySelector("span");
    const handlePad = event => {
      event.preventDefault();
      const point = event.touches?.[0] || event;
      const rect = pad.getBoundingClientRect();
      let dx = point.clientX - (rect.left + rect.width / 2);
      let dy = point.clientY - (rect.top + rect.height / 2);
      const length = Math.hypot(dx, dy);
      if (length > 34) { dx = dx / length * 34; dy = dy / length * 34; }
      state.mobileMove.x = dx / 34;
      state.mobileMove.y = dy / 34;
      knob.style.transform = `translate(${dx}px, ${dy}px)`;
    };
    const resetPad = event => {
      event.preventDefault();
      state.mobileMove.x = 0; state.mobileMove.y = 0;
      knob.style.transform = "translate(0, 0)";
    };
    pad.addEventListener("touchstart", handlePad, { passive: false });
    pad.addEventListener("touchmove", handlePad, { passive: false });
    pad.addEventListener("touchend", resetPad, { passive: false });
    $("#touch-fire").addEventListener("touchstart", event => { event.preventDefault(); state.firing = true; }, { passive: false });
    $("#touch-fire").addEventListener("touchend", event => { event.preventDefault(); state.firing = false; }, { passive: false });
    $("#touch-swap").addEventListener("click", () => switchWeaponSlot((state.player.weaponSlot + 1) % 3));
    $("#touch-dash").addEventListener("click", dash);
  }

  function resize() {
    const ratio = Math.min(devicePixelRatio || 1, 1.5);
    canvas.width = Math.max(640, Math.floor(canvas.clientWidth * ratio));
    canvas.height = Math.max(360, Math.floor(canvas.clientHeight * ratio));
    zBuffer = new Float32Array(canvas.width);
    if (state.mode === "menu") drawBackdrop();
  }

  function randomFreePosition(minDistance = 5) {
    for (let attempt = 0; attempt < 120; attempt++) {
      const x = 1.5 + Math.floor(Math.random() * (MAP_SIZE - 3));
      const y = 1.5 + Math.floor(Math.random() * (MAP_SIZE - 3));
      if (canStand(x, y, 0.35) && Math.hypot(x - state.player.x, y - state.player.y) > minDistance && lineClear(x, y, x + 0.2, y + 0.2)) return { x, y };
    }
    return { x: 20.5, y: 20.5 };
  }

  function spawnWave() {
    const count = Math.min(5 + state.wave * 2, 23);
    const pool = ["scout", "raider"];
    if (state.wave >= 2) pool.push("drone");
    if (state.wave >= 3) pool.push("heavy");
    for (let i = 0; i < count; i++) {
      let kind = pool[Math.floor(Math.random() * pool.length)];
      if (state.wave % 5 === 0 && i === count - 1) kind = "elite";
      const pos = randomFreePosition(6);
      const def = enemyKinds[kind];
      state.enemies.push({
        x: pos.x, y: pos.y, kind, hp: def.hp + state.wave * (kind === "elite" ? 12 : 3), maxHp: def.hp + state.wave * (kind === "elite" ? 12 : 3),
        shootTimer: 400 + Math.random() * 900, hurt: 0, bob: Math.random() * TAU, id: Math.random()
      });
    }
    state.wavePending = false;
    updateHUD();
  }

  function update(dt, now) {
    if (state.mode !== "playing") return;
    const player = state.player;
    let forward = (state.keys.KeyW || state.keys.ArrowUp ? 1 : 0) - (state.keys.KeyS || state.keys.ArrowDown ? 1 : 0) - state.mobileMove.y;
    let strafe = (state.keys.KeyD ? 1 : 0) - (state.keys.KeyA ? 1 : 0) + state.mobileMove.x;
    let turn = (state.keys.ArrowRight ? 1 : 0) - (state.keys.ArrowLeft ? 1 : 0);
    player.angle += turn * dt * 1.9;
    const moveLength = Math.hypot(forward, strafe) || 1;
    forward /= moveLength; strafe /= moveLength;
    const moveSpeed = player.speed * dt;
    const dx = (Math.cos(player.angle) * forward + Math.cos(player.angle + Math.PI / 2) * strafe) * moveSpeed;
    const dy = (Math.sin(player.angle) * forward + Math.sin(player.angle + Math.PI / 2) * strafe) * moveSpeed;
    if (canStand(player.x + dx, player.y, 0.22)) player.x += dx;
    if (canStand(player.x, player.y + dy, 0.22)) player.y += dy;

    if (state.firing) fire(now);
    if (state.reloading && now >= state.reloadEnds) completeReload();
    if (state.comboTimer > 0) state.comboTimer -= dt; else state.combo = 1;
    state.dashCooldown = Math.max(0, state.dashCooldown - dt);
    state.recoil += (0 - state.recoil) * Math.min(1, dt * 10);
    state.shake += (0 - state.shake) * Math.min(1, dt * 12);
    state.muzzle = Math.max(0, state.muzzle - dt * 7);
    player.shieldDelay = Math.max(0, player.shieldDelay - dt);
    if (player.shieldDelay === 0 && player.shield < player.maxShield) player.shield = Math.min(player.maxShield, player.shield + dt * 6);

    updateEnemies(dt);
    updateProjectiles(dt);
    updatePickups(dt);
    updateParticles(dt);

    if (!state.enemies.length && !state.wavePending) {
      state.wavePending = true;
      showAnnouncement("区域清空 // 下一波正在接近", 1700);
      setTimeout(() => {
        if (state.mode === "playing" && state.wavePending) {
          state.wave++;
          spawnWave();
          showAnnouncement(`第 ${state.wave} 波 // ${state.wave % 5 === 0 ? "精英警报" : "守住阵地"}`);
        }
      }, 1900);
    }
    updateHUD();
  }

  function dash() {
    if (state.mode !== "playing" || state.dashCooldown > 0) return;
    const p = state.player;
    const distance = heroes[state.selectedHero].id === "scout" ? 1.8 : 1.35;
    const nx = p.x + Math.cos(p.angle) * distance;
    const ny = p.y + Math.sin(p.angle) * distance;
    if (canStand(nx, p.y)) p.x = nx;
    if (canStand(p.x, ny)) p.y = ny;
    state.dashCooldown = heroes[state.selectedHero].id === "scout" ? 1.15 : 1.8;
    state.shake = 5;
    addBurst(canvas.width / 2, canvas.height * 0.72, heroes[state.selectedHero].color, 16, 6);
    tone(145, 0.09, "sawtooth", 0.035);
  }

  function fire(now) {
    const p = state.player;
    const weapon = weapons[p.weapon];
    if (state.reloading || now - state.lastShot < weapon.cooldown) return;
    if (p.ammo[p.weapon] <= 0) { reload(); return; }
    state.lastShot = now;
    p.ammo[p.weapon]--;
    state.shots++;
    state.recoil = weapon.kick;
    state.shake = weapon.kick * 0.18;
    state.muzzle = 1;
    $("#crosshair").classList.add("firing");
    setTimeout(() => $("#crosshair").classList.remove("firing"), 65);
    let anyHit = false;
    for (let pellet = 0; pellet < weapon.pellets; pellet++) {
      const shotAngle = p.angle + (Math.random() - 0.5) * weapon.spread * 2;
      const hit = traceShot(shotAngle, weapon.range);
      if (hit) {
        hit.enemy.hp -= weapon.damage * (1 - hit.distance / (weapon.range * 2.4));
        hit.enemy.hurt = 0.13;
        anyHit = true;
        const projected = projectPoint(hit.enemy.x, hit.enemy.y);
        if (projected) addBurst(projected.x, projected.y, weapon.color, weapon.pellets > 1 ? 3 : 8, 5);
        if (hit.enemy.hp <= 0) defeatEnemy(hit.enemy, projected);
      }
    }
    if (anyHit) {
      state.hits++;
      $("#hit-marker").classList.remove("active");
      void $("#hit-marker").offsetWidth;
      $("#hit-marker").classList.add("active");
      tone(690, 0.025, "square", 0.025);
    }
    tone(weapon.pitch, weapon.cooldown / 2200, weapon.form === 3 ? "square" : "sawtooth", weapon.form === 2 ? 0.075 : 0.045);
    updateHUD();
  }

  function traceShot(angle, range) {
    let best = null;
    for (const enemy of state.enemies) {
      const dx = enemy.x - state.player.x;
      const dy = enemy.y - state.player.y;
      const distance = Math.hypot(dx, dy);
      if (distance > range || !lineClear(state.player.x, state.player.y, enemy.x, enemy.y)) continue;
      const angleDiff = Math.abs(normAngle(Math.atan2(dy, dx) - angle));
      const threshold = Math.atan2(enemyKinds[enemy.kind].size * 0.38, distance);
      if (angleDiff <= threshold && (!best || distance < best.distance)) best = { enemy, distance };
    }
    return best;
  }

  function defeatEnemy(enemy, projected) {
    if (!state.enemies.includes(enemy)) return;
    const def = enemyKinds[enemy.kind];
    state.enemies.splice(state.enemies.indexOf(enemy), 1);
    state.combo = state.comboTimer > 0 ? Math.min(8, state.combo + 1) : 1;
    state.comboTimer = 3.2;
    state.score += def.score * state.combo;
    if (projected) addBurst(projected.x, projected.y, def.color, enemy.kind === "elite" ? 55 : 28, enemy.kind === "elite" ? 12 : 8);
    state.shake = enemy.kind === "elite" ? 12 : 5;
    tone(enemy.kind === "elite" ? 65 : 92, 0.16, "sawtooth", 0.05);
    if (Math.random() < 0.22 || enemy.kind === "elite") {
      const types = ["health", "shield", "ammo"];
      state.pickups.push({ x: enemy.x, y: enemy.y, type: types[Math.floor(Math.random() * types.length)], bob: 0, life: 15 });
    }
  }

  function reload() {
    if (state.mode !== "playing" || state.reloading) return;
    const p = state.player, weapon = weapons[p.weapon];
    if (p.ammo[p.weapon] >= weapon.mag || p.reserve[p.weapon] <= 0) return;
    state.reloading = true;
    state.reloadEnds = performance.now() + weapon.reload;
    $("#weapon-label").textContent = "装填中…";
    tone(230, 0.05, "triangle", 0.025);
    setTimeout(() => tone(360, 0.04, "triangle", 0.02), weapon.reload * 0.56);
  }

  function completeReload() {
    const p = state.player, weapon = weapons[p.weapon];
    const needed = weapon.mag - p.ammo[p.weapon];
    const amount = Math.min(needed, p.reserve[p.weapon]);
    p.ammo[p.weapon] += amount;
    p.reserve[p.weapon] -= amount;
    state.reloading = false;
    tone(520, 0.05, "triangle", 0.03);
  }

  function switchWeaponSlot(slotIndex) {
    if (!state.player || state.mode !== "playing" || !weapons[state.loadout[slotIndex]]) return;
    state.player.weaponSlot = slotIndex;
    state.player.weapon = state.loadout[slotIndex];
    state.reloading = false;
    tone(320 + slotIndex * 70, 0.045, "triangle", 0.025);
    updateHUD();
  }

  function updateEnemies(dt) {
    const p = state.player;
    for (const enemy of state.enemies) {
      const def = enemyKinds[enemy.kind];
      enemy.hurt = Math.max(0, enemy.hurt - dt);
      enemy.bob += dt * (enemy.kind === "drone" ? 5 : 2.5);
      enemy.shootTimer -= dt * 1000;
      const dx = p.x - enemy.x, dy = p.y - enemy.y;
      const distance = Math.hypot(dx, dy);
      if (distance > 1.05) {
        const move = def.speed * dt * (distance < def.range ? 0.3 : 1);
        const nx = enemy.x + dx / distance * move;
        const ny = enemy.y + dy / distance * move;
        if (canStand(nx, enemy.y, 0.28) && !enemyCrowded(enemy, nx, enemy.y)) enemy.x = nx;
        else {
          const sideX = -dy / distance * move;
          if (canStand(enemy.x + sideX, enemy.y, 0.28)) enemy.x += sideX;
        }
        if (canStand(enemy.x, ny, 0.28) && !enemyCrowded(enemy, enemy.x, ny)) enemy.y = ny;
      }
      if (distance < def.range && enemy.shootTimer <= 0 && lineClear(enemy.x, enemy.y, p.x, p.y)) {
        enemy.shootTimer = def.cooldown * (0.82 + Math.random() * 0.5);
        const speed = enemy.kind === "elite" ? 5.2 : 4.1;
        const accuracy = enemy.kind === "scout" ? 0.09 : 0.055;
        const angle = Math.atan2(dy, dx) + (Math.random() - 0.5) * accuracy;
        state.projectiles.push({ x: enemy.x, y: enemy.y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed, damage: def.damage, color: def.color, life: 2.8 });
        tone(enemy.kind === "elite" ? 155 : 205, 0.055, "square", 0.015);
      }
    }
  }

  function enemyCrowded(source, x, y) {
    return state.enemies.some(other => other !== source && Math.hypot(other.x - x, other.y - y) < 0.48);
  }

  function updateProjectiles(dt) {
    for (let i = state.projectiles.length - 1; i >= 0; i--) {
      const shot = state.projectiles[i];
      shot.life -= dt;
      const nx = shot.x + shot.vx * dt, ny = shot.y + shot.vy * dt;
      if (shot.life <= 0 || isWall(nx, ny)) { state.projectiles.splice(i, 1); continue; }
      shot.x = nx; shot.y = ny;
      if (Math.hypot(shot.x - state.player.x, shot.y - state.player.y) < 0.28) {
        damagePlayer(shot.damage);
        state.projectiles.splice(i, 1);
      }
    }
  }

  function damagePlayer(amount) {
    const p = state.player;
    p.shieldDelay = 3;
    const absorbed = Math.min(p.shield, amount);
    p.shield -= absorbed;
    p.hp -= amount - absorbed;
    state.shake = Math.max(state.shake, 8);
    $("#damage-flash").classList.add("active");
    setTimeout(() => $("#damage-flash").classList.remove("active"), 110);
    tone(74, 0.12, "sawtooth", 0.055);
    if (p.hp <= 0) { p.hp = 0; updateHUD(); endGame(); }
  }

  function updatePickups(dt) {
    for (let i = state.pickups.length - 1; i >= 0; i--) {
      const item = state.pickups[i];
      item.bob += dt * 3; item.life -= dt;
      if (item.life <= 0) { state.pickups.splice(i, 1); continue; }
      if (Math.hypot(item.x - state.player.x, item.y - state.player.y) < 0.7) {
        if (item.type === "health") state.player.hp = Math.min(state.player.maxHp, state.player.hp + 36);
        if (item.type === "shield") state.player.shield = Math.min(state.player.maxShield, state.player.shield + 32);
        if (item.type === "ammo") state.player.reserve = state.player.reserve.map((amount, j) => Math.min(weapons[j].reserve, amount + Math.ceil(weapons[j].mag * 1.2)));
        showAnnouncement(item.type === "health" ? "生命模块 +36" : item.type === "shield" ? "护盾模块 +32" : "弹药补给已获取", 900);
        tone(620, 0.12, "sine", 0.045);
        state.pickups.splice(i, 1);
      }
    }
  }

  function addBurst(x, y, color, count, speed) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * TAU;
      const velocity = Math.random() * speed + 1;
      state.particles.push({ x, y, vx: Math.cos(angle) * velocity, vy: Math.sin(angle) * velocity, life: 0.35 + Math.random() * 0.5, maxLife: 0.85, color, size: 1.5 + Math.random() * 4 });
    }
  }

  function updateParticles(dt) {
    for (let i = state.particles.length - 1; i >= 0; i--) {
      const p = state.particles[i];
      p.life -= dt;
      if (p.life <= 0) { state.particles.splice(i, 1); continue; }
      p.x += p.vx * dt * 60;
      p.y += p.vy * dt * 60;
      p.vx *= 0.94; p.vy *= 0.94;
    }
  }

  function castRay(angle) {
    const posX = state.player.x, posY = state.player.y;
    const rayX = Math.cos(angle), rayY = Math.sin(angle);
    let mapX = Math.floor(posX), mapY = Math.floor(posY);
    const deltaX = Math.abs(1 / (rayX || 0.000001));
    const deltaY = Math.abs(1 / (rayY || 0.000001));
    const stepX = rayX < 0 ? -1 : 1, stepY = rayY < 0 ? -1 : 1;
    let sideX = rayX < 0 ? (posX - mapX) * deltaX : (mapX + 1 - posX) * deltaX;
    let sideY = rayY < 0 ? (posY - mapY) * deltaY : (mapY + 1 - posY) * deltaY;
    let side = 0, cell = 0;
    for (let guard = 0; guard < 64; guard++) {
      if (sideX < sideY) { sideX += deltaX; mapX += stepX; side = 0; }
      else { sideY += deltaY; mapY += stepY; side = 1; }
      cell = state.map[mapY]?.[mapX] || 0;
      if (cell) break;
    }
    const distance = side === 0 ? (mapX - posX + (1 - stepX) / 2) / (rayX || 0.000001) : (mapY - posY + (1 - stepY) / 2) / (rayY || 0.000001);
    const hitCoord = side === 0 ? posY + distance * rayY : posX + distance * rayX;
    return { distance: Math.abs(distance), side, cell, textureX: hitCoord - Math.floor(hitCoord) };
  }

  function render() {
    if (state.mode === "menu") return;
    const width = canvas.width, height = canvas.height;
    const mapDef = maps[state.selectedMap];
    const shakeX = (Math.random() - 0.5) * state.shake;
    const shakeY = (Math.random() - 0.5) * state.shake;
    ctx.save();
    ctx.translate(shakeX, shakeY);

    const sky = ctx.createLinearGradient(0, 0, 0, height * 0.52);
    sky.addColorStop(0, mapDef.sky[0]); sky.addColorStop(1, mapDef.sky[1]);
    ctx.fillStyle = sky; ctx.fillRect(-20, -20, width + 40, height * 0.54 + 20);
    drawSkyDetails(mapDef, width, height);
    const floor = ctx.createLinearGradient(0, height * 0.48, 0, height);
    floor.addColorStop(0, mapDef.floor[1]); floor.addColorStop(1, mapDef.floor[0]);
    ctx.fillStyle = floor; ctx.fillRect(-20, height * 0.5, width + 40, height * 0.53);
    drawFloorGrid(mapDef, width, height);

    const horizon = height * 0.5 + state.recoil * 0.45;
    for (let x = 0; x < width; x += RAY_STEP) {
      const rayAngle = state.player.angle - FOV / 2 + (x / width) * FOV;
      const hit = castRay(rayAngle);
      const corrected = Math.max(0.001, hit.distance * Math.cos(rayAngle - state.player.angle));
      const wallHeight = Math.min(height * 2.3, height / corrected);
      const top = horizon - wallHeight / 2;
      const base = mapDef.walls[hit.cell === 2 ? 1 : 0];
      const shade = clamp(1 - corrected / 26 - hit.side * 0.13, 0.22, 1);
      ctx.fillStyle = shadeColor(base, shade);
      ctx.fillRect(x, top, RAY_STEP + 0.5, wallHeight);
      if ((Math.floor(hit.textureX * 8) === 0 || Math.floor(hit.textureX * 8) === 7) && corrected < 11) {
        ctx.fillStyle = shadeColor(hit.cell === 2 ? mapDef.color : mapDef.walls[2], shade * 0.8);
        ctx.fillRect(x, top, RAY_STEP + 0.5, wallHeight);
      }
      for (let s = 0; s < RAY_STEP && x + s < width; s++) zBuffer[x + s] = corrected;
    }

    renderWorldSprites(width, height, horizon);
    renderParticles();
    renderWeapon(width, height);
    if (state.muzzle > 0) renderMuzzle(width, height);
    ctx.restore();
    drawMinimap();
  }

  function drawSkyDetails(mapDef, width, height) {
    ctx.save();
    ctx.globalAlpha = 0.65;
    for (let i = 0; i < 34; i++) {
      const x = seeded(i * 7 + mapDef.seed) * width;
      const y = seeded(i * 13 + mapDef.seed) * height * 0.42;
      const size = 0.7 + seeded(i * 19) * 1.7;
      ctx.fillStyle = i % 5 === 0 ? mapDef.color : "#d9f5ff";
      ctx.fillRect(x, y, size, size);
    }
    ctx.globalAlpha = 0.12;
    ctx.fillStyle = mapDef.color;
    for (let i = 0; i < 5; i++) ctx.fillRect((i * width / 5 - state.player.angle * 60) % width, height * (0.2 + i * 0.045), width * 0.18, 1);
    ctx.restore();
  }

  function drawFloorGrid(mapDef, width, height) {
    ctx.save();
    ctx.strokeStyle = mapDef.color;
    ctx.globalAlpha = 0.09;
    ctx.lineWidth = 1;
    for (let i = 1; i < 13; i++) {
      const y = height * 0.5 + (i * i / 144) * height * 0.5;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }
    const offset = (state.player.x + state.player.y) % 1;
    for (let i = -8; i <= 8; i++) {
      ctx.beginPath(); ctx.moveTo(width / 2, height * 0.5); ctx.lineTo(width / 2 + (i + offset) * width * 0.18, height); ctx.stroke();
    }
    ctx.restore();
  }

  function shadeColor(hex, factor) {
    const value = parseInt(hex.slice(1), 16);
    const r = (value >> 16) & 255, g = (value >> 8) & 255, b = value & 255;
    return `rgb(${Math.round(r * factor)},${Math.round(g * factor)},${Math.round(b * factor)})`;
  }

  function projectPoint(x, y) {
    const dx = x - state.player.x, dy = y - state.player.y;
    const depth = dx * Math.cos(state.player.angle) + dy * Math.sin(state.player.angle);
    if (depth <= 0.08) return null;
    const side = -dx * Math.sin(state.player.angle) + dy * Math.cos(state.player.angle);
    return { x: canvas.width * (0.5 + side / (depth * 2 * Math.tan(FOV / 2))), y: canvas.height * 0.5, depth };
  }

  function renderWorldSprites(width, height, horizon) {
    const sprites = [];
    for (const enemy of state.enemies) sprites.push({ ...enemy, spriteType: "enemy", depth: Math.hypot(enemy.x - state.player.x, enemy.y - state.player.y) });
    for (const pickup of state.pickups) sprites.push({ ...pickup, spriteType: "pickup", depth: Math.hypot(pickup.x - state.player.x, pickup.y - state.player.y), size: 0.44 });
    for (const shot of state.projectiles) sprites.push({ ...shot, spriteType: "projectile", depth: Math.hypot(shot.x - state.player.x, shot.y - state.player.y), size: 0.18 });
    sprites.sort((a, b) => b.depth - a.depth);
    state.renderedEnemies = [];
    for (const sprite of sprites) {
      const projected = projectPoint(sprite.x, sprite.y);
      if (!projected || projected.depth > 28) continue;
      const kindSize = sprite.spriteType === "enemy" ? enemyKinds[sprite.kind].size : sprite.size;
      const drawHeight = height / projected.depth * kindSize;
      const drawWidth = drawHeight * (sprite.spriteType === "enemy" ? 0.72 : 0.68);
      const bob = sprite.spriteType === "enemy" ? Math.sin(sprite.bob) * drawHeight * (sprite.kind === "drone" ? 0.08 : 0.015) : Math.sin(sprite.bob || performance.now() / 260) * drawHeight * 0.08;
      const left = projected.x - drawWidth / 2;
      const top = horizon - drawHeight * (sprite.spriteType === "projectile" ? 0.12 : 0.54) + bob;
      if (left > width || left + drawWidth < 0) continue;
      const texture = getTexture(sprite);
      ctx.save();
      if (sprite.spriteType !== "enemy") ctx.globalCompositeOperation = "lighter";
      for (let screenX = Math.max(0, Math.floor(left)); screenX < Math.min(width, Math.ceil(left + drawWidth)); screenX += 2) {
        if (projected.depth < zBuffer[Math.floor(screenX)] + 0.12) {
          const tx = clamp(Math.floor((screenX - left) / drawWidth * texture.width), 0, texture.width - 1);
          ctx.drawImage(texture, tx, 0, 1, texture.height, screenX, top, 2.2, drawHeight);
        }
      }
      ctx.restore();
      if (sprite.spriteType === "enemy" && projected.depth < 12 && sprite.hp < sprite.maxHp) {
        const barWidth = Math.min(70, drawWidth * 0.72);
        ctx.fillStyle = "rgba(0,0,0,.65)";
        ctx.fillRect(projected.x - barWidth / 2, top - 9, barWidth, 4);
        ctx.fillStyle = sprite.kind === "elite" ? "#ae75ff" : "#ff5e83";
        ctx.fillRect(projected.x - barWidth / 2, top - 9, barWidth * clamp(sprite.hp / sprite.maxHp, 0, 1), 4);
      }
    }
  }

  function getTexture(sprite) {
    const key = sprite.spriteType === "enemy" ? `${sprite.kind}-${sprite.hurt > 0}` : `${sprite.spriteType}-${sprite.type || sprite.color}`;
    if (spriteTextures[key]) return spriteTextures[key];
    const c = document.createElement("canvas"); c.width = 96; c.height = 128;
    const g = c.getContext("2d");
    g.clearRect(0, 0, 96, 128);
    if (sprite.spriteType === "enemy") drawEnemyTexture(g, sprite.kind, sprite.hurt > 0);
    else if (sprite.spriteType === "pickup") drawPickupTexture(g, sprite.type);
    else drawProjectileTexture(g, sprite.color);
    spriteTextures[key] = c;
    return c;
  }

  function drawEnemyTexture(g, kind, hurt) {
    const def = enemyKinds[kind];
    const color = hurt ? "#ffffff" : def.color;
    g.save();
    g.shadowColor = color; g.shadowBlur = 18;
    if (kind === "drone" || kind === "scout") {
      g.fillStyle = color;
      g.beginPath(); g.moveTo(12,60); g.lineTo(34,43); g.lineTo(62,43); g.lineTo(84,60); g.lineTo(63,70); g.lineTo(56,91); g.lineTo(40,91); g.lineTo(33,70); g.closePath(); g.fill();
      g.fillStyle = "#07101d"; g.fillRect(34,54,28,12);
      g.fillStyle = "#fff"; g.fillRect(43,57,10,5);
      g.strokeStyle = color; g.lineWidth = 5; g.beginPath(); g.moveTo(18,58); g.lineTo(5,76); g.moveTo(78,58); g.lineTo(91,76); g.stroke();
    } else {
      const heavy = kind === "heavy" || kind === "elite";
      g.fillStyle = color;
      g.fillRect(heavy ? 24 : 29, 22, heavy ? 48 : 38, 28);
      g.fillRect(heavy ? 18 : 23, 51, heavy ? 60 : 50, heavy ? 49 : 43);
      g.fillRect(heavy ? 9 : 13, 56, heavy ? 11 : 9, 39);
      g.fillRect(heavy ? 76 : 74, 56, heavy ? 11 : 9, 39);
      g.fillRect(heavy ? 25 : 29, 97, heavy ? 16 : 13, 27);
      g.fillRect(heavy ? 55 : 54, 97, heavy ? 16 : 13, 27);
      g.fillStyle = "#07101d"; g.fillRect(30,30,36,12); g.fillRect(heavy ? 27 : 31,59,heavy ? 42 : 34,25);
      g.fillStyle = "#f8ffff"; g.fillRect(37,34,22,4);
      if (kind === "elite") { g.strokeStyle = "#efe2ff"; g.lineWidth = 4; g.strokeRect(14,13,68,91); }
    }
    g.restore();
  }

  function drawPickupTexture(g, type) {
    const color = type === "health" ? "#b8ff59" : type === "shield" ? "#25e7ff" : "#ffce45";
    g.save(); g.translate(48,64); g.shadowColor = color; g.shadowBlur = 24;
    g.fillStyle = color; g.strokeStyle = "#efffff"; g.lineWidth = 3;
    g.beginPath();
    for (let i = 0; i < 6; i++) { const a = Math.PI / 3 * i - Math.PI / 6; const x = Math.cos(a) * 27, y = Math.sin(a) * 27; i ? g.lineTo(x,y) : g.moveTo(x,y); }
    g.closePath(); g.fill(); g.stroke();
    g.fillStyle = "#07101d";
    if (type === "health") { g.fillRect(-5,-17,10,34); g.fillRect(-17,-5,34,10); }
    else if (type === "shield") { g.beginPath(); g.arc(0,0,13,0,TAU); g.strokeStyle="#07101d"; g.lineWidth=6; g.stroke(); }
    else { g.fillRect(-14,-9,28,18); g.fillStyle=color; g.fillRect(-8,-4,4,8); g.fillRect(3,-4,4,8); }
    g.restore();
  }

  function drawProjectileTexture(g, color) {
    const gradient = g.createRadialGradient(48,64,1,48,64,34);
    gradient.addColorStop(0,"#fff"); gradient.addColorStop(.18,color); gradient.addColorStop(1,"transparent");
    g.fillStyle = gradient; g.fillRect(10,26,76,76);
  }

  function renderParticles() {
    ctx.save(); ctx.globalCompositeOperation = "lighter";
    for (const p of state.particles) {
      ctx.globalAlpha = clamp(p.life / p.maxLife, 0, 1);
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color; ctx.shadowBlur = 10;
      ctx.fillRect(p.x, p.y, p.size, p.size);
    }
    ctx.restore();
  }

  function renderWeapon(width, height) {
    const weapon = weapons[state.player.weapon];
    const hero = heroes[state.selectedHero];
    const moveBob = (state.keys.KeyW || state.keys.KeyS || state.mobileMove.y) ? Math.sin(performance.now() / 105) * 5 : 0;
    const x = width / 2 + state.recoil * 1.5;
    const y = height + state.recoil * 2 + moveBob;
    ctx.save();
    ctx.translate(x, y);
    ctx.shadowColor = weapon.color; ctx.shadowBlur = state.muzzle > 0 ? 24 : 8;
    ctx.fillStyle = "#07101b";
    ctx.strokeStyle = weapon.color;
    ctx.lineWidth = Math.max(2, width / 600);
    const scale = clamp(width / 960, 0.7, 1.45);
    ctx.scale(scale, scale);
    ctx.beginPath();
    if (weapon.form === 1) { ctx.moveTo(-132,-6); ctx.lineTo(-94,-106); ctx.lineTo(72,-112); ctx.lineTo(138,-20); }
    else if (weapon.form === 2) { ctx.moveTo(-88,-4); ctx.lineTo(-70,-118); ctx.lineTo(112,-92); ctx.lineTo(128,-10); }
    else { ctx.moveTo(-102,-2); ctx.lineTo(-82,-96); ctx.lineTo(82,-104); ctx.lineTo(112,-8); }
    ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = weapon.color;
    ctx.fillRect(-52,-84,98,weapon.form === 2 ? 8 : 12);
    ctx.fillStyle = hero.color;
    ctx.fillRect(-26,-47,52,10);
    ctx.fillStyle = "rgba(255,255,255,.7)";
    ctx.fillRect(48,-88,38,3);
    ctx.restore();
  }

  function renderMuzzle(width, height) {
    const weapon = weapons[state.player.weapon];
    const gradient = ctx.createRadialGradient(width / 2 + 65, height * 0.74, 2, width / 2 + 65, height * 0.74, 90 * state.muzzle);
    gradient.addColorStop(0, "#fff"); gradient.addColorStop(0.16, weapon.color); gradient.addColorStop(1, "transparent");
    ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.fillStyle = gradient; ctx.fillRect(width / 2 - 40, height * 0.56, 210, 210); ctx.restore();
  }

  function drawMinimap() {
    const size = minimap.width, cell = size / MAP_SIZE;
    mctx.clearRect(0, 0, size, size);
    mctx.fillStyle = "rgba(3,8,18,.88)"; mctx.fillRect(0,0,size,size);
    mctx.fillStyle = maps[state.selectedMap].color + "55";
    for (let y = 0; y < MAP_SIZE; y++) for (let x = 0; x < MAP_SIZE; x++) if (state.map[y][x]) mctx.fillRect(x * cell, y * cell, cell + .4, cell + .4);
    mctx.fillStyle = "#ff5878";
    for (const enemy of state.enemies) { mctx.beginPath(); mctx.arc(enemy.x * cell, enemy.y * cell, enemy.kind === "elite" ? 3.8 : 2.2, 0, TAU); mctx.fill(); }
    mctx.fillStyle = "#b8ff59";
    for (const item of state.pickups) { mctx.fillRect(item.x * cell - 1.5, item.y * cell - 1.5, 3, 3); }
    const p = state.player;
    mctx.save(); mctx.translate(p.x * cell, p.y * cell); mctx.rotate(p.angle);
    mctx.fillStyle = "#fff"; mctx.beginPath(); mctx.moveTo(6,0); mctx.lineTo(-4,-4); mctx.lineTo(-2,0); mctx.lineTo(-4,4); mctx.closePath(); mctx.fill(); mctx.restore();
    mctx.strokeStyle = maps[state.selectedMap].color + "99"; mctx.lineWidth = 2; mctx.strokeRect(1,1,size-2,size-2);
  }

  function updateHUD() {
    if (!state.player) return;
    const p = state.player, hero = heroes[state.selectedHero], weapon = weapons[p.weapon];
    $("#map-label").textContent = maps[state.selectedMap].name;
    $("#wave-label").textContent = `第 ${state.wave} 波`;
    $("#enemy-count").textContent = `目标 ${state.enemies.length}`;
    $("#score-label").textContent = String(state.score).padStart(6,"0");
    $("#combo-label").textContent = `x${state.combo} 连击`;
    $("#hero-monogram").textContent = hero.mark;
    $("#hero-monogram").style.color = hero.color;
    $("#hero-monogram").style.borderColor = hero.color;
    $("#hero-label").textContent = hero.name;
    $("#health-label").textContent = Math.ceil(p.hp);
    $("#health-bar").style.transform = `scaleX(${clamp(p.hp / p.maxHp, 0, 1)})`;
    $("#shield-bar").style.transform = `scaleX(${clamp(p.shield / p.maxShield, 0, 1)})`;
    $("#weapon-label").textContent = state.reloading ? "装填中…" : weapon.name;
    $("#ammo-label").textContent = p.ammo[p.weapon];
    $("#reserve-label").textContent = ` / ${p.reserve[p.weapon]}`;
    document.querySelectorAll(".weapon-slot").forEach((el, i) => {
      el.classList.toggle("active", i === p.weaponSlot);
      el.style.setProperty("--slot-color", weapons[state.loadout[i]].color);
    });
  }

  function showAnnouncement(message, duration = 1400) {
    const el = $("#announcement");
    el.textContent = message;
    el.classList.add("active");
    clearTimeout(state.announcementTimer);
    state.announcementTimer = setTimeout(() => el.classList.remove("active"), duration);
  }

  function drawBackdrop() {
    const width = canvas.width || innerWidth, height = canvas.height || innerHeight;
    const gradient = ctx.createLinearGradient(0,0,width,height);
    gradient.addColorStop(0,"#071528"); gradient.addColorStop(.48,"#060a15"); gradient.addColorStop(1,"#170b2c");
    ctx.fillStyle = gradient; ctx.fillRect(0,0,width,height);
    ctx.save(); ctx.globalCompositeOperation="lighter";
    for (let i=0;i<55;i++) {
      const x=seeded(i*13+4)*width, y=seeded(i*23+9)*height, r=seeded(i*31+7)*2+0.4;
      ctx.fillStyle=i%7===0?"#25e7ff":"#7d8fb5"; ctx.globalAlpha=.18+seeded(i)*.5; ctx.fillRect(x,y,r,r);
    }
    ctx.restore();
  }

  function initAudio() {
    if (!state.sound || state.audio) return;
    try { state.audio = new (window.AudioContext || window.webkitAudioContext)(); } catch { state.sound = false; }
  }

  function tone(frequency, duration, type = "sine", volume = 0.03) {
    if (!state.sound) return;
    initAudio();
    if (!state.audio) return;
    const start = state.audio.currentTime;
    const oscillator = state.audio.createOscillator();
    const gain = state.audio.createGain();
    oscillator.type = type; oscillator.frequency.setValueAtTime(frequency, start);
    oscillator.frequency.exponentialRampToValueAtTime(Math.max(30, frequency * 0.55), start + duration);
    gain.gain.setValueAtTime(volume, start); gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    oscillator.connect(gain); gain.connect(state.audio.destination);
    oscillator.start(start); oscillator.stop(start + duration);
  }

  function toggleSound() {
    state.sound = !state.sound;
    $("#sound-button").textContent = state.sound ? "声音" : "静音";
    if (state.sound) tone(440, .06, "sine", .03);
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await $("#game-shell").requestFullscreen();
    } catch { showAnnouncement("当前浏览器不支持全屏", 1000); }
  }

  function gameLoop(now) {
    const dt = Math.min(0.035, Math.max(0, (now - state.lastTime) / 1000 || 0));
    state.lastTime = now;
    update(dt, now);
    if (state.mode !== "menu") render();
    requestAnimationFrame(gameLoop);
  }

  initUI();
  requestAnimationFrame(gameLoop);
})();
