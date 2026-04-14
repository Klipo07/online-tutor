// Экран «Мои занятия» — список предстоящих и прошедших бронирований
import { useCallback, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from "react-native";
import { Stack, useRouter, useFocusEffect } from "expo-router";
import api from "../services/api";
import { Colors } from "../constants/theme";

type BookingSession = {
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
  payment_status: string;
  agora_channel_name: string | null;
  created_at: string;
};

type FilterKey = "upcoming" | "past" | "cancelled";

const STATUS_LABEL: Record<BookingSession["status"], string> = {
  pending: "Ожидает подтверждения",
  confirmed: "Подтверждено",
  completed: "Завершено",
  cancelled: "Отменено",
};

const STATUS_COLOR: Record<BookingSession["status"], string> = {
  pending: Colors.warning,
  confirmed: Colors.primary,
  completed: Colors.success,
  cancelled: Colors.error,
};

function formatDateTime(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", weekday: "short" }),
    time: d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }),
  };
}

export default function MySessionsScreen() {
  const router = useRouter();
  const [sessions, setSessions] = useState<BookingSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<FilterKey>("upcoming");

  const load = useCallback(async () => {
    try {
      const res = await api.get("/sessions");
      setSessions(res.data.sessions);
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить занятия");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    load();
  }, [load]);

  const now = Date.now();
  const filtered = sessions.filter((s) => {
    const isPast = new Date(s.scheduled_at).getTime() < now || s.status === "completed";
    if (filter === "cancelled") return s.status === "cancelled";
    if (filter === "upcoming") return !isPast && s.status !== "cancelled";
    return isPast && s.status !== "cancelled";
  });

  const cancelSession = (session: BookingSession) => {
    Alert.alert(
      "Отменить занятие?",
      `${session.subject_name} с ${session.tutor_name}`,
      [
        { text: "Нет", style: "cancel" },
        {
          text: "Отменить",
          style: "destructive",
          onPress: async () => {
            try {
              await api.put(`/sessions/${session.id}/cancel`);
              load();
            } catch (e: any) {
              const msg = e.response?.data?.detail || "Не удалось отменить";
              Alert.alert("Ошибка", msg);
            }
          },
        },
      ]
    );
  };

  const renderItem = useCallback(
    ({ item }: { item: BookingSession }) => {
      const { date, time } = formatDateTime(item.scheduled_at);
      const canCancel = item.status === "pending" || item.status === "confirmed";
      return (
        <TouchableOpacity
          style={styles.card}
          activeOpacity={0.85}
          onPress={() => router.push(`/session/${item.id}`)}
        >
          <View style={styles.cardHeader}>
            <Text style={styles.subject}>{item.subject_name}</Text>
            <View style={[styles.statusBadge, { backgroundColor: STATUS_COLOR[item.status] + "22" }]}>
              <Text style={[styles.statusText, { color: STATUS_COLOR[item.status] }]}>
                {STATUS_LABEL[item.status]}
              </Text>
            </View>
          </View>
          <Text style={styles.tutor}>с {item.tutor_name}</Text>
          <View style={styles.metaRow}>
            <Text style={styles.meta}>📅 {date}</Text>
            <Text style={styles.meta}>🕑 {time}</Text>
            <Text style={styles.meta}>⏱ {item.duration_minutes} мин</Text>
          </View>
          <View style={styles.cardFooter}>
            <Text style={styles.price}>{item.price.toFixed(0)} ₽</Text>
            {canCancel && (
              <TouchableOpacity onPress={() => cancelSession(item)}>
                <Text style={styles.cancelBtn}>Отменить</Text>
              </TouchableOpacity>
            )}
          </View>
        </TouchableOpacity>
      );
    },
    [router]
  );

  return (
    <>
      <Stack.Screen options={{ title: "Мои занятия" }} />
      <View style={styles.container}>
        <View style={styles.filterRow}>
          {(["upcoming", "past", "cancelled"] as FilterKey[]).map((k) => (
            <TouchableOpacity
              key={k}
              style={[styles.filterChip, filter === k && styles.filterChipActive]}
              onPress={() => setFilter(k)}
            >
              <Text style={[styles.filterText, filter === k && styles.filterTextActive]}>
                {k === "upcoming" ? "Предстоящие" : k === "past" ? "Прошедшие" : "Отменённые"}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {loading ? (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={Colors.primary} />
          </View>
        ) : filtered.length === 0 ? (
          <View style={styles.centered}>
            <Text style={styles.emptyIcon}>📅</Text>
            <Text style={styles.emptyText}>
              {filter === "upcoming" ? "Нет предстоящих занятий" : filter === "past" ? "Ещё нет прошедших" : "Нет отменённых"}
            </Text>
            {filter === "upcoming" && (
              <TouchableOpacity
                style={styles.ctaButton}
                onPress={() => router.push("/(tabs)/tutors")}
              >
                <Text style={styles.ctaText}>Найти репетитора</Text>
              </TouchableOpacity>
            )}
          </View>
        ) : (
          <FlatList
            data={filtered}
            renderItem={renderItem}
            keyExtractor={(s) => s.id.toString()}
            contentContainerStyle={{ padding: 16 }}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
          />
        )}
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  filterRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 4,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  filterChipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  filterText: { fontSize: 13, color: Colors.textSecondary, fontWeight: "500" },
  filterTextActive: { color: "#fff" },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 15, color: Colors.textSecondary, marginBottom: 16 },
  ctaButton: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: Colors.primary,
  },
  ctaText: { color: "#fff", fontWeight: "700", fontSize: 14 },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  subject: { fontSize: 16, fontWeight: "700", color: Colors.text, flex: 1 },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: { fontSize: 11, fontWeight: "700" },
  tutor: { fontSize: 13, color: Colors.textSecondary, marginTop: 4 },
  metaRow: { flexDirection: "row", gap: 14, marginTop: 10, flexWrap: "wrap" },
  meta: { fontSize: 12, color: Colors.text },
  cardFooter: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  price: { fontSize: 15, fontWeight: "700", color: Colors.primary },
  cancelBtn: { fontSize: 13, color: Colors.error, fontWeight: "600" },
});
