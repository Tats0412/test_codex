import { StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Line, Polyline } from "react-native-svg";

const WIDTH = 320;
const HEIGHT = 110;
const PAD = 12;

export function TrendChart({ scores, title }) {
  if (!scores || scores.length < 2) return null;

  const xScale = (i) =>
    PAD + (i / (scores.length - 1)) * (WIDTH - 2 * PAD);
  const yScale = (s) => HEIGHT - PAD - (s / 100) * (HEIGHT - 2 * PAD);

  const points = scores
    .map((s, i) => `${xScale(i).toFixed(1)},${yScale(s).toFixed(1)}`)
    .join(" ");

  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title || "スコア推移"}</Text>
      <Svg width={WIDTH} height={HEIGHT}>
        {[25, 50, 75].map((y) => (
          <Line
            key={y}
            x1={PAD}
            y1={yScale(y)}
            x2={WIDTH - PAD}
            y2={yScale(y)}
            stroke="#2a315a"
            strokeWidth="1"
            strokeDasharray="2,4"
          />
        ))}
        <Polyline
          points={points}
          fill="none"
          stroke="#8ef0c1"
          strokeWidth="2"
        />
        {scores.map((s, i) => (
          <Circle
            key={i}
            cx={xScale(i)}
            cy={yScale(s)}
            r="3"
            fill="#8ef0c1"
          />
        ))}
      </Svg>
      <View style={styles.axis}>
        <Text style={styles.axisLabel}>古い</Text>
        <Text style={styles.axisLabel}>最新</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#141a33",
    padding: 12,
    borderRadius: 14,
    marginBottom: 12,
  },
  title: { color: "#9bb0ff", fontSize: 13, fontWeight: "600", marginBottom: 6 },
  axis: { flexDirection: "row", justifyContent: "space-between" },
  axisLabel: { color: "#6d7bb0", fontSize: 11 },
});
