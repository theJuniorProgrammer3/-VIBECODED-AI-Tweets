let tokens = [];
let patchMap = {};
let patches = [];
let patchMeaningful = [];

let memori = [];
let memoriSet = new Set();

const kapasitas_memori = 5;
const panjang_patch = 7;

// ================= LOAD =================
async function loadData() {
  const res = await fetch("data.json");
  const data = await res.json();

  tokens = data.tokens;
  patchMap = data.patch_map;

  // rebuild patches
  for (let i = 0; i < tokens.length - panjang_patch; i++) {
    const p = tokens.slice(i, i + panjang_patch);
    patches.push(p);
    patchMeaningful.push(kataBermakna(p));
  }

  initMemori();
}

// ================= UTIL =================

function kataBermakna(tokens) {
  const tanda = new Set([".", ",", "!", "?", ";", ":"]);
  return tokens.filter(t => !tanda.has(t));
}

function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

// ================= MEMORI =================

function initMemori() {
  const kata = tokens.filter(t => ![".", ",", "!", "?", ";", ":"].includes(t));

  while (memori.length < kapasitas_memori) {
    let k = randomChoice(kata);
    if (!memoriSet.has(k)) {
      memori.push(k);
      memoriSet.add(k);
    }
  }
}

function updateMemori(buffer) {
  for (let i = 0; i < 15; i++) {
    let k = pilihKataBias(buffer);

    if (k && !memoriSet.has(k) && k.length > 3) {
      if (memori.length >= kapasitas_memori) {
        let old = memori.shift();
        memoriSet.delete(old);
      }
      memori.push(k);
      memoriSet.add(k);
      return;
    }
  }
}

// ================= SCORING =================

function skorMemori(patch) {
  let s = 0;
  for (let k of patch) {
    if (memoriSet.has(k)) s++;
  }
  return s;
}

function cariKataDekat(patchIdx) {
  const kataPatch = new Set(patchMeaningful[patchIdx]);

  for (let m of memori) {
    let posMem = [];
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i] === m) posMem.push(i);
    }

    for (let p of kataPatch) {
      let posP = [];
      for (let i = 0; i < tokens.length; i++) {
        if (tokens[i] === p) posP.push(i);
      }

      for (let pm of posMem) {
        for (let pp of posP) {
          if (Math.abs(pm - pp) <= 10) return 1;
        }
      }
    }
  }

  return 0;
}

// ================= BIAS =================

function pilihKataBias(buffer) {
  let kata = kataBermakna(buffer);
  if (!kata.length) return null;

  let n = kata.length;
  if (n <= 2) return randomChoice(kata);

  let weights = [];
  for (let i = 0; i < n; i++) {
    weights.push(1.0 - (0.4 * Math.min(i, n - 1 - i) / Math.floor(n / 2)));
  }

  let sum = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * sum;

  for (let i = 0; i < n; i++) {
    r -= weights[i];
    if (r <= 0) return kata[i];
  }

  return kata[0];
}

// ================= GENERATE =================

function generateText(target = 30) {
  let buffer = [...randomChoice(patches)];

  while (buffer.length < target) {
    let last = buffer[buffer.length - 1];
    let kandidat = patchMap[last];

    if (!kandidat) break;

    if (kandidat.length > 200) {
      kandidat = kandidat.sort(() => 0.5 - Math.random()).slice(0, 200);
    }

    let best = kandidat[0];
    let bestScore = -1;

    for (let idx of kandidat) {
      let s = skorMemori(patches[idx]);
      if (s > bestScore) {
        bestScore = s;
        best = idx;
      }
    }

    let patch = patches[best];
    buffer.push(...patch.slice(1));

    updateMemori(buffer);
  }

  return buffer.join(" ");
}

// ================= UI =================

function generateTweet() {
  let tweet = generateText(20 + Math.floor(Math.random() * 20));

  let div = document.createElement("div");
  div.className = "tweet";
  div.innerText = tweet;

  document.getElementById("feed").prepend(div);
}

loadData();
