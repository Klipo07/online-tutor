// Экран управления расписанием репетитора — часы работы по дням недели
import { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import api from "../../services/api";
import { Colors } from "../../constants/theme";

type DayKey = "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun";
type Schedule = Record<DayKey, [number, number] | null>;

const DAYS: { key: DayKey; label: string }[] = [
  { key: "mon", label: "Понедельник" },
  { key: "tue", label: "Вторник" },
  { key: "wed", label: "Среда" },
  { key: "thu", label: "Четверг" },
  { key: "fri", label: "Пятница" },
  { key: "sat", label: "Суббота" },
  { key: "sun", label: "Воскресенье" },
];

const DEFAULT_RANGE: [number, number] = [9, 21];

export default function TutorScheduleScreen() {
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await api.get<Schedule>("/tutors/me/schedule");
      setSchedule(res.data);
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить расписание");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const toggleDay = (day: DayKey) => {
    if (!schedule) return;
    setSchedule({
      ...schedule,
      [day]: schedule[day] === null ? DEFAULT_RANGE : null,
    });
  };

  const adjustHour = (day: DayKey, which: 0 | 1, delta: number) => {
    if (!schedule) return;
    const current = schedule[day];
    if (!current) return;
    const next: [number, number] = [current[0], current[1]];
    next[which] = Math.max(0, Math.min(24, next[which] + delta));
    // Запрещаем инвертирование (start >= end)
    if (next[0] >= next[1]) return;
    setSchedule({ ...schedule, [day]: next });
  };

  const save = async () => {
    if (!schedule) return;
    setSaving(true);
    try {
      await api.put("/tutors/me/schedule", schedule);
      Alert.alert("Сохранено", "Расписание обновлено");
    } catch (e: any) {
      const msg = e?.response?.data?.detail || "Не удалось сохранить расписание";
      Alert.alert("Ошибка", typeof msg === "string" ? msg : "Проверьте введённые часы");
    } finally {
      setSaving(false);
    }
  };

  if (loading || !schedule) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.hint}>
        Отметьте рабочие часы. Ученики увидят свободные слоты только в эти интервалы.
      </Text>

      {DAYS.map(({ key, label }) => {
        const range = schedule[key];
        const isWorking = range !== null;
        return (
          <View key={key} style={styles.dayCard}>
            <View style={styles.dayHeader}>
              <Text style={styles.dayLabel}>{label}</Text>
              <TouchableOpacity
                style={[styles.toggle, isWorking && styles.toggleActive]}
                onPress={() => toggleDay(key)}
              >
                <Text style={[styles.toggleText, isWorking && styles.toggleTextActive]}>
                  {isWorking ? "Рабочий" : "Выходной"}
                </Text>
              </TouchableOpacity>
            </View>

            {isWorking && range && (
              <View style={styles.rangeRow}>
                <View style={styles.hourBox}>
                  <Text style={styles.hourLabel}>с</Text>
                  <View style={styles.stepper}>
                    <TouchableOpacity
                      onPress={() => adjustHour(key, 0, -1)}
                      style={styles.stepBtn}
                    >
                      <Text style={styles.stepText}>−</Text>
                    </TouchableOpacity>
                    <Text style={styles.hourValue}>{String(range[0]).padStart(2, "0")}:00</Text>
                    <TouchableOpacity
                      onPress={() => adjustHour(key, 0, 1)}
                      style={styles.stepBtn}
                    >
                      <Text style={styles.stepText}>+</Text>
                    </TouchableOpacity>
                  </View>
                </View>

                <View style={styles.hourBox}>
                  <Text style={styles.hourLabel}>до</Text>
                  <View style={styles.stepper}>
                    <TouchableOpacity
                      onPress={() => adjustHour(key, 1, -1)}
                      style={styles.stepBtn}
                    >
                      <Text style={styles.stepText}>−</Text>
                    </TouchableOpacity>
                    <Text style={styles.hourValue}>{String(range[1]).padStart(2, "0")}:00</Text>
                    <TouchableOpacity
                      onPress={() => adjustHour(key, 1, 1)}
                      style={styles.stepBtn}
                    >
                      <Text style={styles.stepText}>+</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            )}
          </View>
        );
      })}

      <TouchableOpacity
        style={[styles.saveBtn, saving && { opacity: 0.5 }]}
        onPress={save}
        disabled={saving}
      >
        <Text style={styles.saveBtnText}>
          {saving ? "Сохранение..." : "Сохранить расписание"}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 40 },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.background },
  hint: { fontSize: 13, color: Colors.textSecondary, marginBottom: 16, lineHeight: 18 },

  dayCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  dayHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  dayLabel: { fontSize: 15, fontWeight: "600", color: Colors.text },
  toggle: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 14,
    backgroundColor: Colors.inputBg,
  },
  toggleActive: { backgroundColor: Colors.primary + "20" },
  toggleText: { fontSize: 12, fontWeight: "600", color: Colors.textSecondary },
  toggleTextActive: { color: Colors.primary },

  rangeRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 12,
  },
  hourBox: { flex: 1 },
  hourLabel: { fontSize: 12, color: Colors.textSecondary, marginBottom: 6 },
  stepper: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    paddingHorizontal: 6,
  },
  stepBtn: { paddingHorizontal: 10, paddingVertical: 8 },
  stepText: { fontSize: 20, color: Colors.primary, fontWeight: "700" },
  hourValue: { fontSize: 16, fontWeight: "700", color: Colors.text },

  saveBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginTop: 16,
  },
  saveBtnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
});
