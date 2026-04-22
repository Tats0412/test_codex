import * as DocumentPicker from "expo-document-picker";
import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";

import { analyzeRecording } from "./src/api";
import { FeedbackView } from "./src/FeedbackView";
import { HistoryScreen } from "./src/HistoryScreen";
import { LevelMeter } from "./src/LevelMeter";
import { usePlayer } from "./src/Player";
import { useRecorder } from "./src/Recorder";
import { SongSuggest } from "./src/SongSuggest";

function formatElapsed(ms) {
  const total = Math.floor(ms / 1000);
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

export default function App() {
  const recorder = useRecorder();
  const player = usePlayer();
  const [songTitle, setSongTitle] = useState("");
  const [artist, setArtist] = useState("");
  const [userNote, setUserNote] = useState("");
  const [recordingUri, setRecordingUri] = useState(null);
  const [referenceUri, setReferenceUri] = useState(null);
  const [referenceName, setReferenceName] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [screen, setScreen] = useState("home"); // home | history

  async function handleToggleRecord() {
    try {
      if (recorder.isRecording) {
        const uri = await recorder.stop();
        setRecordingUri(uri);
      } else {
        setRecordingUri(null);
        setResult(null);
        await recorder.start();
      }
    } catch (e) {
      Alert.alert("録音エラー", e.message || String(e));
    }
  }

  async function handlePickReference() {
    try {
      const res = await DocumentPicker.getDocumentAsync({
        type: "audio/*",
        copyToCacheDirectory: true,
      });
      if (res.canceled) return;
      const asset = res.assets?.[0];
      if (!asset) return;
      setReferenceUri(asset.uri);
      setReferenceName(asset.name || "reference");
    } catch (e) {
      Alert.alert("選択に失敗", e.message || String(e));
    }
  }

  async function handlePlayRecording() {
    if (player.isPlaying) {
      await player.stop();
    } else if (recordingUri) {
      try {
        await player.play(recordingUri);
      } catch (e) {
        Alert.alert("再生エラー", e.message || String(e));
      }
    }
  }

  async function handleAnalyze() {
    if (!recordingUri) {
      Alert.alert("録音がありません", "先にマイクボタンで録音してください。");
      return;
    }
    if (!songTitle.trim()) {
      Alert.alert("曲名が必要です", "どの曲を練習したか教えてください。");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeRecording({
        uri: recordingUri,
        referenceUri,
        songTitle: songTitle.trim(),
        artist: artist.trim(),
        userNote: userNote.trim(),
      });
      setResult(data);
    } catch (e) {
      Alert.alert("解析に失敗しました", e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  if (screen === "history") {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.safe} edges={["top", "left", "right"]}>
          <StatusBar style="light" />
          <HistoryScreen onClose={() => setScreen("home")} />
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safe} edges={["top", "left", "right"]}>
        <StatusBar style="light" />
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === "ios" ? "padding" : undefined}
        >
          <ScrollView
            contentContainerStyle={styles.container}
            keyboardShouldPersistTaps="handled"
          >
            <View style={styles.topRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.title}>AI ボーカルコーチ</Text>
                <Text style={styles.subtitle}>
                  歌った録音を送ると、曲に合わせたアドバイスが届きます
                </Text>
              </View>
              <Pressable
                style={styles.historyButton}
                onPress={() => setScreen("history")}
              >
                <Text style={styles.historyButtonText}>履歴</Text>
              </Pressable>
            </View>

            <View style={styles.form}>
              <Text style={styles.label}>曲名 *</Text>
              <TextInput
                style={styles.input}
                placeholder="例: 夜に駆ける"
                placeholderTextColor="#6d7bb0"
                value={songTitle}
                onChangeText={setSongTitle}
              />
              <SongSuggest
                query={songTitle}
                onPick={(s) => {
                  setSongTitle(s.song_title);
                  if (s.artist) setArtist(s.artist);
                }}
              />

              <Text style={styles.label}>アーティスト</Text>
              <TextInput
                style={styles.input}
                placeholder="例: YOASOBI"
                placeholderTextColor="#6d7bb0"
                value={artist}
                onChangeText={setArtist}
              />

              <Text style={styles.label}>気になっているポイント(任意)</Text>
              <TextInput
                style={[styles.input, styles.multiline]}
                placeholder="例: サビの高音が苦しい"
                placeholderTextColor="#6d7bb0"
                multiline
                value={userNote}
                onChangeText={setUserNote}
              />
            </View>

            <Pressable
              style={[
                styles.recordButton,
                recorder.isRecording && styles.recordButtonActive,
              ]}
              onPress={handleToggleRecord}
            >
              <Text style={styles.recordButtonText}>
                {recorder.isRecording ? "■ 停止" : "● 録音開始"}
              </Text>
              {recorder.isRecording ? (
                <>
                  <Text style={styles.timer}>
                    {formatElapsed(recorder.elapsedMs)}
                  </Text>
                  <LevelMeter level={recorder.level} />
                </>
              ) : recordingUri ? (
                <Text style={styles.timerDone}>録音済み</Text>
              ) : null}
            </Pressable>

            {recordingUri && !recorder.isRecording ? (
              <Pressable style={styles.miniButton} onPress={handlePlayRecording}>
                <Text style={styles.miniButtonText}>
                  {player.isPlaying ? "■ 停止" : "▶ 録音を再生"}
                </Text>
              </Pressable>
            ) : null}

            <Pressable style={styles.miniButton} onPress={handlePickReference}>
              <Text style={styles.miniButtonText}>
                {referenceName
                  ? `お手本: ${referenceName}`
                  : "お手本音源を選ぶ(任意)"}
              </Text>
              {referenceName ? (
                <Pressable
                  onPress={() => {
                    setReferenceUri(null);
                    setReferenceName("");
                  }}
                >
                  <Text style={styles.clearX}>×</Text>
                </Pressable>
              ) : null}
            </Pressable>

            <Pressable
              style={[
                styles.analyzeButton,
                (!recordingUri || loading) && styles.analyzeButtonDisabled,
              ]}
              onPress={handleAnalyze}
              disabled={!recordingUri || loading}
            >
              {loading ? (
                <ActivityIndicator color="#0b1020" />
              ) : (
                <Text style={styles.analyzeButtonText}>AIに聴いてもらう</Text>
              )}
            </Pressable>

            <FeedbackView data={result} />
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0b1020" },
  container: { padding: 20, paddingBottom: 60 },
  topRow: { flexDirection: "row", alignItems: "flex-start", gap: 12 },
  title: { color: "#ffffff", fontSize: 26, fontWeight: "700" },
  subtitle: { color: "#9bb0ff", marginTop: 6, marginBottom: 18 },
  historyButton: {
    backgroundColor: "#1b2650",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
  },
  historyButtonText: { color: "#ffffff", fontSize: 13, fontWeight: "600" },
  form: { gap: 6, marginBottom: 18 },
  label: { color: "#9bb0ff", fontSize: 13, marginTop: 6 },
  input: {
    backgroundColor: "#141a33",
    color: "#ffffff",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
  },
  multiline: { minHeight: 70, textAlignVertical: "top" },
  recordButton: {
    backgroundColor: "#1b2650",
    paddingVertical: 18,
    borderRadius: 14,
    alignItems: "center",
    gap: 4,
  },
  recordButtonActive: { backgroundColor: "#5a1b36" },
  recordButtonText: { color: "#ffffff", fontSize: 18, fontWeight: "600" },
  timer: { color: "#ff9fb6", fontSize: 14, fontVariant: ["tabular-nums"] },
  timerDone: { color: "#8ef0c1", fontSize: 13 },
  miniButton: {
    marginTop: 10,
    backgroundColor: "#141a33",
    paddingVertical: 12,
    borderRadius: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  miniButtonText: { color: "#ffffff", fontSize: 14 },
  clearX: { color: "#ff9fb6", fontSize: 18, paddingHorizontal: 8 },
  analyzeButton: {
    marginTop: 12,
    backgroundColor: "#7aa2ff",
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: "center",
  },
  analyzeButtonDisabled: { opacity: 0.4 },
  analyzeButtonText: { color: "#0b1020", fontSize: 16, fontWeight: "700" },
});
