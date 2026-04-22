import { useEffect, useRef, useState } from "react";
import { Audio } from "expo-av";

export function useRecorder() {
  const recordingRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [level, setLevel] = useState(0); // 0..1 normalized input level
  const tickRef = useRef(null);

  useEffect(() => {
    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync().catch(() => {});
      }
    };
  }, []);

  async function start() {
    const perm = await Audio.requestPermissionsAsync();
    if (!perm.granted) throw new Error("マイクの権限が必要です");

    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
    });

    const { recording } = await Audio.Recording.createAsync(
      Audio.RecordingOptionsPresets.HIGH_QUALITY,
      (status) => {
        if (status.metering != null) {
          // metering is dBFS (typically -160..0). Map to 0..1.
          const db = status.metering;
          const normalized = Math.max(0, Math.min(1, (db + 60) / 60));
          setLevel(normalized);
        }
      },
      100, // update every 100ms
    );
    recordingRef.current = recording;
    setElapsedMs(0);
    setIsRecording(true);
    const startedAt = Date.now();
    tickRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startedAt);
    }, 250);
  }

  async function stop() {
    if (!recordingRef.current) return null;
    clearInterval(tickRef.current);
    tickRef.current = null;

    try {
      await recordingRef.current.stopAndUnloadAsync();
    } catch (_) {}

    const uri = recordingRef.current.getURI();
    recordingRef.current = null;
    setIsRecording(false);
    setLevel(0);
    return uri;
  }

  return { isRecording, elapsedMs, level, start, stop };
}
