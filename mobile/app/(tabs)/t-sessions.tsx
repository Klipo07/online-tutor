// Экран занятий репетитора — три фильтра: предстоящие / сегодня / история
import { useCallback, useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import api from "../../services/api";
import { Colors } from "../../constants/theme";

type SessionItem = {
  id: number;
  student_id: number;
  tutor_id: number;
  subject_id: number;
  tutor_name: string;
  subject_name: string;
  scheduled_at: string;
  duration_minutes: number;
  status: "pending" | "confirmed" | "completed" | "cancelled";
  price: number;
};

type Filter = "upcoming" | "today" | "history";

function sameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function formatDay(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);
  if (sameDay(d, today)) return "Сегодня";
  if (sameDay(d, tomorrow)) return "Завтра";
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

const STATUS_LABEL: Record<SessionItem["status"], string> = {
  pending: "Ожидает",
  confirmed: "Подтверждено",
  completed: "Проведено",
  cancelled: "Отменено",
};

const STATUS_COLOR: Record<SessionItem["status"], string> = {
  pending: "#FFB84D",
  confirmed: "#4CAF8F",
  completed: "#8B8B8B",
  cancelled: "#E53935",
};

export default function TutorSessionsScreen() {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<Filter>("upcoming");

  const load = useCallback(async () => {
    try {
      const res = await api.get<{ sessions: SessionItem[] }>("/sessions");
      setSessions(res.data.sessions);
    } catch {
      // Пропускаем — оставим пустой список
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const filtered = useMemo(() => {
    const now = new Date();
    const today = new Date();
    if (filter === "today") {
      return sessions.filter(
        (s) => sameDay(new Date(s.scheduled_at), today) && s.status !== "cancelled"
      );
    }
    if (filter === "upcoming") {
      return sessions.filter(
        (s) =>
          new Date(s.scheduled_at) >= now &&
          (s.status === "pending" || s.status === "confirmed")
      );
    }
    // history — прошедшие или отменённые
    return sessions.filter(
      (s) => new Date(s.scheduled_at) < now || s.status === "cancelled"
    );
  }, [sessions, filter]);

  const renderItem = useCallback(
    ({ item }: { item: SessionItem }) => (
      <TouchableOpacity
        style={styles.card}
        onPress={() => router.push(`/session/${item.id}`)}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.cardDay}>{formatDay(item.scheduled_at)}</Text>
          <Text style={styles.cardTime}>{formatTime(item.scheduled_at)}</Text>
        </View>
        <Text style={styles.cardSubject}>{item.subject_name}</Text>
        <View style={styles.cardFooter}>
          <View
            style={[
              styles.statusPill,
              { backgroundColor: STATUS_COLOR[item.status] + "20" },
            ]}
          >
            <Text style={[styles.statusText, { color: STATUS_COLOR[item.status] }]}>
              {STATUS_LABEL[item.status]}
            </Text>
          </View>
          <Text style={styles.cardPrice}>{item.price.toLocaleString("ru-RU")} ₽</Text>
        </View>
      </TouchableOpacity>
    ),
    [router]
  );

  return (
    <View style={styles.container}>
      {/* Фильтры */}
      <View style={styles.filters}>
        {([
          ["upcoming", "Предстоящие"],
          ["today", "Сегодня"],
          ["history", "История"],
        ] as const).map(([key, label]) => (
          <TouchableOpacity
            key={key}
            style={[styles.filterChip, filter === key && styles.filterChipActive]}
            onPress={() => setFilter(key)}
          >
            <Text
              style={[
                styles.filterText,
                filter === key && styles.filterTextActive,
              ]}
            >
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : filtered.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyIcon}>📅</Text>
          <Text style={styles.emptyTitle}>
            {filter === "today"
              ? "На сегодня занятий нет"
              : filter === "upcoming"
              ? "Нет предстоящих занятий"
              : "История пуста"}
          </Text>
          <Text style={styles.emptySub}>
            {filter === "upcoming"
              ? "Ученики увидят вас в маркетплейсе и смогут записаться"
              : ""}
          </Text>
        </View>
      ) : (
        <FlatList
          data={filtered}
          renderItem={renderItem}
          keyExtractor={(i) => String(i.id)}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  filters: {
    flexDirection: "row",
    padding: 16,
    gap: 8,
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  filterChip: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: Colors.inputBg,
    alignItems: "center",
  },
  filterChipActive: { backgroundColor: Colors.primary },
  filterText: { fontSize: 13, color: Colors.textSecondary, fontWeight: "600" },
  filterTextActive: { color: "#fff" },

  list: { padding: 16 },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  cardDay: { fontSize: 15, fontWeight: "700", color: Colors.text },
  cardTime: { fontSize: 15, fontWeight: "700", color: Colors.primary },
  cardSubject: { fontSize: 13, color: Colors.textSecondary, marginBottom: 10 },
  cardFooter: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  statusPill: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  statusText: { fontSize: 12, fontWeight: "600" },
  cardPrice: { fontSize: 14, fontWeight: "700", color: Colors.text },

  center: { flex: 1, justifyContent: "center", alignItems: "center", padding: 32 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 17, fontWeight: "700", color: Colors.text, textAlign: "center" },
  emptySub: { fontSize: 14, color: Colors.textSecondary, marginTop: 6, textAlign: "center" },
});
