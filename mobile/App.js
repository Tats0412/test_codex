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
import { useRecorder } from "./src/Recorder";

function formatElapsed(ms) {
  const total = Math.floor(ms / 1000);
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

export default function App() {
  const recorder = useRecorder();
  const [songTitle, setSongTitle] = useState("");
  const [artist, setArtist] = useState("");
  const [userNote, setUserNote] = useState("");
  const [recordingUri, setRecordingUri] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

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
            <Text style={styles.title}>AI ボーカルコーチ</Text>
            <Text style={styles.subtitle}>
              歌った録音を送ると、曲に合わせたアドバイスが届きます
            </Text>

            <View style={styles.form}>
              <Text style={styles.label}>曲名 *</Text>
              <TextInput
                style={styles.input}
                placeholder="例: 夜に駆ける"
                placeholderTextColor="#6d7bb0"
                value={songTitle}
                onChangeText={setSongTitle}
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
                <Text style={styles.timer}>
                  {formatElapsed(recorder.elapsedMs)}
                </Text>
              ) : recordingUri ? (
                <Text style={styles.timerDone}>録音済み</Text>
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
  title: { color: "#ffffff", fontSize: 26, fontWeight: "700" },
  subtitle: { color: "#9bb0ff", marginTop: 6, marginBottom: 18 },
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
