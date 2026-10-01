// Change API_BASE if the backend runs on a different origin (e.g. "http://127.0.0.1:8000")
const API_BASE = window.ASR_API_BASE || "";

const $ = (id) => document.getElementById(id);
const dropzone = $("dropzone"), fileInput = $("fileInput"), recordBtn = $("recordBtn");
const timerEl = $("timer"), selected = $("selected"), fileNameEl = $("fileName"), player = $("player");
const transcribeBtn = $("transcribeBtn"), statusEl = $("status");
const resultEl = $("result"), transcriptEl = $("transcript"), metaEl = $("meta"), segmentsEl = $("segments");

let currentFile = null;      // File or Blob
let currentName = "";
let lastResult = null;
let recorder = null, chunks = [], timerId = null, startedAt = 0;

function setStatus(msg, kind = "") { statusEl.textContent = msg; statusEl.className = "status " + kind; }

function setFile(file, name) {
  currentFile = file; currentName = name;
  fileNameEl.textContent = name;
  if (player.src) URL.revokeObjectURL(player.src);
  player.src = URL.createObjectURL(file);
  selected.hidden = false;
  transcribeBtn.disabled = false;
  setStatus("");
}

// ---------- File selection ----------
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") fileInput.click(); });
fileInput.addEventListener("change", () => { if (fileInput.files[0]) setFile(fileInput.files[0], fileInput.files[0].name); });
["dragenter", "dragover"].forEach((ev) => dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.add("drag"); }));
["dragleave", "drop"].forEach((ev) => dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.remove("drag"); }));
dropzone.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) setFile(f, f.name); });

// ---------- Microphone recording ----------
function fmtTime(s) { return String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(Math.floor(s % 60)).padStart(2, "0"); }

recordBtn.addEventListener("click", async () => {
  if (recorder && recorder.state === "recording") { recorder.stop(); return; }
  if (!navigator.mediaDevices || !window.MediaRecorder) { setStatus("Recording is not supported in this browser.", "error"); return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream);
    chunks = [];
    recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      clearInterval(timerId);
      timerEl.hidden = true;
      recordBtn.textContent = "🔴 Record from microphone";
      recordBtn.classList.remove("recording");
      const type = recorder.mimeType || "audio/webm";
      const ext = type.includes("mp4") ? "m4a" : type.includes("ogg") ? "ogg" : "webm";
      setFile(new Blob(chunks, { type }), `recording.${ext}`);
    };
    recorder.start();
    startedAt = Date.now();
    timerEl.hidden = false; timerEl.textContent = "00:00";
    timerId = setInterval(() => (timerEl.textContent = fmtTime((Date.now() - startedAt) / 1000)), 250);
    recordBtn.textContent = "⏹ Stop recording";
    recordBtn.classList.add("recording");
    setStatus("");
  } catch (err) {
    setStatus("Microphone access denied or unavailable.", "error");
  }
});

// ---------- Transcribe ----------
transcribeBtn.addEventListener("click", async () => {
  if (!currentFile) return;
  const form = new FormData();
  form.append("file", currentFile, currentName);
  form.append("model", $("model").value);
  form.append("language", $("language").value);
  form.append("task", $("translate").checked ? "translate" : "transcribe");

  transcribeBtn.disabled = true;
  resultEl.hidden = true;
  setStatus("Transcribing… the first run downloads the model, so it may take a while.", "busy");
  try {
    const res = await fetch(`${API_BASE}/api/transcribe`, { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `Server error (${res.status})`);
    lastResult = data;
    renderResult(data);
    setStatus("Done ✔");
  } catch (err) {
    setStatus(err.message || "Request failed. Is the backend running?", "error");
  } finally {
    transcribeBtn.disabled = false;
  }
});

function renderResult(d) {
  transcriptEl.value = d.text || "(No speech detected)";
  metaEl.textContent = `Language: ${d.language} · Duration: ${d.duration}s · ${d.segments.length} segments`;
  segmentsEl.innerHTML = "";
  d.segments.forEach((s) => {
    const li = document.createElement("li");
    const t = document.createElement("span"); t.className = "t"; t.textContent = fmtTime(s.start);
    const x = document.createElement("span"); x.textContent = s.text;
    li.append(t, x);
    li.title = "Click to play from here";
    li.addEventListener("click", () => { player.currentTime = s.start; player.play(); });
    segmentsEl.appendChild(li);
  });
  resultEl.hidden = false;
  resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------- Copy / download ----------
$("copyBtn").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(transcriptEl.value); setStatus("Copied to clipboard ✔"); }
  catch { transcriptEl.select(); document.execCommand("copy"); }
});

document.querySelectorAll("[data-dl]").forEach((btn) =>
  btn.addEventListener("click", () => {
    if (!lastResult) return;
    const fmt = btn.dataset.dl;
    const content = fmt === "json" ? JSON.stringify({ language: lastResult.language, text: lastResult.text, segments: lastResult.segments }, null, 2) : lastResult[fmt];
    const base = currentName.replace(/\.[^.]+$/, "") || "transcript";
    const url = URL.createObjectURL(new Blob([content], { type: "text/plain;charset=utf-8" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: `${base}.${fmt}` });
    a.click();
    URL.revokeObjectURL(url);
  })
);
