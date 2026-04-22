import { StyleSheet, View } from "react-native";

const N_BARS = 16;

export function LevelMeter({ level }) {
  const lit = Math.round((level || 0) * N_BARS);
  return (
    <View style={styles.row}>
      {Array.from({ length: N_BARS }).map((_, i) => {
        const active = i < lit;
        const color =
          i < N_BARS * 0.6 ? "#8ef0c1" : i < N_BARS * 0.85 ? "#ffd48a" : "#ff9fb6";
        return (
          <View
            key={i}
            style={[
              styles.bar,
              { backgroundColor: active ? color : "#2a315a" },
            ]}
          />
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    gap: 3,
    marginTop: 10,
    justifyContent: "center",
  },
  bar: { width: 5, height: 20, borderRadius: 2 },
});
