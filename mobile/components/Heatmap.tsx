// Heatmap активности (GitHub-style)
import { memo, useMemo } from "react";
import { View, Text, StyleSheet } from "react-native";
import { Colors } from "../constants/theme";

type ActivityDay = { date: string; count: number };

type Props = {
  data: ActivityDay[];
  cellSize?: number;
  gap?: number;
};

// Цветовая шкала — 5 уровней
const LEVELS = [
  Colors.inputBg, // 0
  "#C7D2FE", // 1
  "#818CF8", // 2
  "#6366F1", // 3
  "#4338CA", // 4
];

const MONTH_LABELS = [
  "Янв",
  "Фев",
  "Мар",
  "Апр",
  "Май",
  "Июн",
  "Июл",
  "Авг",
  "Сен",
  "Окт",
  "Ноя",
  "Дек",
];

function levelFor(count: number): number {
  if (count <= 0) return 0;
  if (count <= 2) return 1;
  if (count <= 5) return 2;
  if (count <= 10) return 3;
  return 4;
}

function HeatmapComponent({ data, cellSize = 12, gap = 3 }: Props) {
  // Группируем по неделям (Пн–Вс). data отсортирована по возрастанию.
  const weeks = useMemo(() => {
    if (data.length === 0) return [] as ActivityDay[][];
    const first = new Date(data[0].date);
    // getDay: 0=Вс..6=Сб. Приводим к 0=Пн..6=Вс
    const dayOfWeek = (first.getDay() + 6) % 7;
    const grid: ActivityDay[][] = [];
    let current: ActivityDay[] = new Array(dayOfWeek).fill(null);
    data.forEach((d) => {
      current.push(d);
      if (current.length === 7) {
        grid.push(current);
        current = [];
      }
    });
    if (current.length > 0) {
      while (current.length < 7) current.push(null as unknown as ActivityDay);
      grid.push(current);
    }
    return grid;
  }, [data]);

  // Подписи месяцев сверху — показываем месяц у той недели, где он начинается
  const monthLabels = useMemo(() => {
    const out: { index: number; label: string }[] = [];
    let lastMonth = -1;
    weeks.forEach((week, idx) => {
      const firstDay = week.find((d) => d);
      if (!firstDay) return;
      const m = new Date(firstDay.date).getMonth();
      if (m !== lastMonth) {
        out.push({ index: idx, label: MONTH_LABELS[m] });
        lastMonth = m;
      }
    });
    return out;
  }, [weeks]);

  const columnWidth = cellSize + gap;

  return (
    <View>
      {/* Подписи месяцев */}
      <View style={styles.monthsRow}>
        {monthLabels.map(({ index, label }) => (
          <Text
            key={`${index}-${label}`}
            style={[styles.monthLabel, { left: index * columnWidth }]}
          >
            {label}
          </Text>
        ))}
      </View>

      <View style={styles.grid}>
        {weeks.map((week, wi) => (
          <View key={wi} style={{ marginRight: gap }}>
            {week.map((day, di) => {
              const level = day ? levelFor(day.count) : 0;
              return (
                <View
                  key={di}
                  style={{
                    width: cellSize,
                    height: cellSize,
                    marginBottom: gap,
                    backgroundColor: day ? LEVELS[level] : "transparent",
                    borderRadius: 2,
                  }}
                />
              );
            })}
          </View>
        ))}
      </View>

      {/* Легенда */}
      <View style={styles.legendRow}>
        <Text style={styles.legendLabel}>Меньше</Text>
        {LEVELS.map((c, i) => (
          <View
            key={i}
            style={{
              width: cellSize,
              height: cellSize,
              backgroundColor: c,
              borderRadius: 2,
              marginHorizontal: 2,
            }}
          />
        ))}
        <Text style={styles.legendLabel}>Больше</Text>
      </View>
    </View>
  );
}

export const Heatmap = memo(HeatmapComponent);

const styles = StyleSheet.create({
  monthsRow: { height: 16, position: "relative", marginBottom: 4 },
  monthLabel: { position: "absolute", fontSize: 10, color: Colors.textSecondary },
  grid: { flexDirection: "row" },
  legendRow: { flexDirection: "row", alignItems: "center", marginTop: 8 },
  legendLabel: { fontSize: 11, color: Colors.textSecondary, marginHorizontal: 6 },
});
