import Constants from "expo-constants";

const DEFAULT_BASE = "http://localhost:8000";

export function getApiBaseUrl() {
  const fromConfig =
    Constants?.expoConfig?.extra?.apiBaseUrl ||
    Constants?.manifest?.extra?.apiBaseUrl;
  return fromConfig || DEFAULT_BASE;
}

export async function analyzeRecording({ uri, songTitle, artist, userNote }) {
  const form = new FormData();
  // React Native FormData accepts {uri, name, type}
  const filename = uri.split("/").pop() || "recording.m4a";
  const ext = filename.split(".").pop().toLowerCase();
  const mime =
    ext === "wav"
      ? "audio/wav"
      : ext === "mp3"
      ? "audio/mpeg"
      : ext === "webm"
      ? "audio/webm"
      : "audio/m4a";

  form.append("audio", { uri, name: filename, type: mime });
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
