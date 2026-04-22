import Constants from "expo-constants";

const DEFAULT_BASE = "http://localhost:8000";

export function getApiBaseUrl() {
  const fromConfig =
    Constants?.expoConfig?.extra?.apiBaseUrl ||
    Constants?.manifest?.extra?.apiBaseUrl;
  return fromConfig || DEFAULT_BASE;
}

function mimeFor(filename) {
  const ext = (filename.split(".").pop() || "").toLowerCase();
  if (ext === "wav") return "audio/wav";
  if (ext === "mp3") return "audio/mpeg";
  if (ext === "webm") return "audio/webm";
  if (ext === "flac") return "audio/flac";
  if (ext === "ogg") return "audio/ogg";
  return "audio/m4a";
}

function appendAudio(form, field, uri, fallbackName) {
  const filename = uri.split("/").pop() || fallbackName;
  form.append(field, { uri, name: filename, type: mimeFor(filename) });
}

export async function analyzeRecording({
  uri,
  referenceUri,
  songTitle,
  artist,
  userNote,
}) {
  const form = new FormData();
  appendAudio(form, "audio", uri, "recording.m4a");
  if (referenceUri) appendAudio(form, "reference", referenceUri, "reference.m4a");
  form.append("song_title", songTitle);
  form.append("artist", artist || "");
  form.append("user_note", userNote || "");

  const res = await fetch(`${getApiBaseUrl()}/analyze`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Analyze failed (${res.status}): ${text || res.statusText}`);
  }
  return res.json();
}

export async function fetchSessions() {
  const res = await fetch(`${getApiBaseUrl()}/sessions`);
  if (!res.ok) throw new Error(`Load sessions failed (${res.status})`);
  const data = await res.json();
  return data.sessions || [];
}

export async function fetchSessionDetail(id) {
  const res = await fetch(`${getApiBaseUrl()}/sessions/${id}`);
  if (!res.ok) throw new Error(`Load session failed (${res.status})`);
  return res.json();
}

export async function deleteSession(id) {
  const res = await fetch(`${getApiBaseUrl()}/sessions/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Delete failed (${res.status})`);
  return res.json();
}
