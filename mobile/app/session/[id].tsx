// Экран занятия — meeting-link flow вместо встроенного видео
// Тьютор вставляет ссылку на Zoom/Meet/Jitsi, ученик её открывает
import { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  TextInput,
  ScrollView,
  Linking,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import api from "../../services/api";
import { useAuthStore } from "../../store/authStore";
import { Colors } from "../../constants/theme";

type SessionData = {
  id: number;
  student_id: number;
  tutor_id: number;
  tutor_name: string;
  student_name: string;
  subject_name: string;
  scheduled_at: string;
  duration_minutes: number;
  status: string;
  meeting_link: string | null;
};

export default function SessionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isTutor = user?.role === "tutor";

  const [session, setSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [linkInput, setLinkInput] = useState("");
  const [saving, setSaving] = useState(false);

  const loadSession = useCallback(async () => {
    try {
      const res = await api.get<SessionData>(`/sessions/${id}`);
      setSession(res.data);
      setLinkInput(res.data.meeting_link || "");
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить данные занятия");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  const saveLink = async () => {
    const trimmed = linkInput.trim();
    // Простая валидация — должен начинаться с http/https
    if (trimmed && !/^https?:\/\//i.test(trimmed)) {
      Alert.alert("Неверная ссылка", "Ссылка должна начинаться с http:// или https://");
      return;
    }
    setSaving(true);
    try {
      const res = await api.put<SessionData>(`/sessions/${id}/meeting-link`, {
        meeting_link: trimmed || null,
      });
      setSession(res.data);
      Alert.alert("Сохранено", trimmed ? "Ученик увидит ссылку" : "Ссылка удалена");
    } catch (e: any) {
      const msg = e?.response?.data?.detail || "Не удалось сохранить";
      Alert.alert("Ошибка", msg);
    } finally {
      setSaving(false);
    }
  };

  const openLink = async () => {
    if (!session?.meeting_link) return;
    const can = await Linking.canOpenURL(session.meeting_link);
    if (!can) {
      Alert.alert("Не удалось открыть", "Проверьте ссылку или установите нужное приложение");
      return;
    }
    await Linking.openURL(session.meeting_link);
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  if (!session) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>Занятие не найдено</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>Назад</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const counterpartyName = isTutor ? session.student_name : session.tutor_name;
  const counterpartyLabel = isTutor ? "Ученик" : "Репетитор";

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 24 }}>
      <View style={styles.sessionInfo}>
        <View style={styles.sessionAvatar}>
          <Text style={styles.sessionAvatarText}>
            {counterpartyName.split(" ").map((n) => n[0]).join("")}
          </Text>
        </View>
        <Text style={styles.counterLabel}>{counterpartyLabel}</Text>
        <Text style={styles.counterName}>{counterpartyName}</Text>
        <Text style={styles.sessionSubject}>{session.subject_name}</Text>
        <Text style={styles.sessionDate}>{formatDate(session.scheduled_at)}</Text>
        <Text style={styles.sessionDuration}>{session.duration_minutes} минут</Text>

        <View
          style={[
            styles.statusBadge,
            session.status === "confirmed" && styles.statusConfirmed,
          ]}
        >
          <Text style={styles.statusText}>
            {session.status === "pending"
              ? "Ожидает подтверждения"
              : session.status === "confirmed"
              ? "Подтверждено"
              : session.status === "completed"
              ? "Завершено"
              : "Отменено"}
          </Text>
        </View>
      </View>

      {/* Блок meeting-link */}
      <View style={styles.linkSection}>
        <Text style={styles.sectionTitle}>Ссылка на занятие</Text>
        <Text style={styles.sectionHint}>
          Zoom / Google Meet / Jitsi / Skype — любая платформа по договорённости
        </Text>

        {isTutor ? (
          // Тьютор — редактирует ссылку
          <>
            <TextInput
              style={styles.input}
              value={linkInput}
              onChangeText={setLinkInput}
              placeholder="https://meet.google.com/..."
              placeholderTextColor={Colors.textSecondary}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
            <TouchableOpacity
              style={[styles.saveBtn, saving && styles.btnDisabled]}
              onPress={saveLink}
              disabled={saving}
            >
              <Text style={styles.saveBtnText}>
                {saving ? "Сохранение..." : "Сохранить ссылку"}
              </Text>
            </TouchableOpacity>
            {session.meeting_link ? (
              <TouchableOpacity style={styles.openBtn} onPress={openLink}>
                <Text style={styles.openBtnText}>Проверить ссылку ↗</Text>
              </TouchableOpacity>
            ) : null}
          </>
        ) : (
          // Ученик — только открывает ссылку или ждёт
          <>
            {session.meeting_link ? (
              <>
                <View style={styles.linkPreview}>
                  <Text style={styles.linkText} numberOfLines={1}>
                    {session.meeting_link}
                  </Text>
                </View>
                <TouchableOpacity style={styles.joinBtn} onPress={openLink}>
                  <Text style={styles.joinBtnText}>Открыть занятие →</Text>
                </TouchableOpacity>
              </>
            ) : (
              <View style={styles.waitingCard}>
                <Text style={styles.waitingText}>
                  Репетитор ещё не прислал ссылку. Загляните ближе к началу занятия.
                </Text>
              </View>
            )}
          </>
        )}
      </View>

      <TouchableOpacity style={styles.cancelButton} onPress={() => router.back()}>
        <Text style={styles.cancelButtonText}>Назад</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: Colors.background,
  },
  errorText: { fontSize: 16, color: Colors.textSecondary, marginBottom: 16 },
  backButton: { padding: 12, borderRadius: 8, backgroundColor: Colors.primary },
  backButtonText: { color: "#fff", fontSize: 14, fontWeight: "600" },

  sessionInfo: { alignItems: "center", paddingTop: 24, paddingBottom: 8 },
  sessionAvatar: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },
  sessionAvatarText: { color: "#fff", fontSize: 28, fontWeight: "700" },
  counterLabel: { fontSize: 12, color: Colors.textSecondary, textTransform: "uppercase" },
  counterName: { fontSize: 20, fontWeight: "700", color: Colors.text, marginTop: 2 },
  sessionSubject: { fontSize: 15, color: Colors.primary, fontWeight: "600", marginTop: 6 },
  sessionDate: { fontSize: 14, color: Colors.textSecondary, marginTop: 8 },
  sessionDuration: { fontSize: 14, color: Colors.textSecondary, marginTop: 2 },
  statusBadge: {
    marginTop: 14,
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: Colors.warning + "20",
  },
  statusConfirmed: { backgroundColor: Colors.success + "20" },
  statusText: { fontSize: 13, fontWeight: "600", color: Colors.text },

  linkSection: {
    marginTop: 24,
    padding: 16,
    backgroundColor: Colors.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: Colors.text },
  sectionHint: { fontSize: 12, color: Colors.textSecondary, marginTop: 4, marginBottom: 12 },
  input: {
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 14,
    color: Colors.text,
  },
  saveBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 10,
    padding: 14,
    alignItems: "center",
    marginTop: 12,
  },
  saveBtnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
  btnDisabled: { opacity: 0.5 },
  openBtn: { padding: 12, alignItems: "center", marginTop: 6 },
  openBtnText: { color: Colors.primary, fontSize: 14, fontWeight: "600" },

  linkPreview: {
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  linkText: { color: Colors.text, fontSize: 13 },
  joinBtn: {
    backgroundColor: Colors.secondary,
    borderRadius: 10,
    padding: 16,
    alignItems: "center",
  },
  joinBtnText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  waitingCard: {
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    padding: 16,
  },
  waitingText: { fontSize: 14, color: Colors.textSecondary, lineHeight: 20 },

  cancelButton: {
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginTop: 16,
  },
  cancelButtonText: { color: Colors.textSecondary, fontSize: 15 },
});
