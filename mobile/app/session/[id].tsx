// Экран видеозанятия — подключение к Agora-каналу
import { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import api from "../../services/api";
import { Colors } from "../../constants/theme";

type SessionData = {
  id: number;
  tutor_name: string;
  subject_name: string;
  scheduled_at: string;
  duration_minutes: number;
  status: string;
  agora_channel_name: string;
};

type VideoToken = {
  token: string;
  channel_name: string;
  uid: number;
  app_id: string;
};

export default function SessionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const [session, setSession] = useState<SessionData | null>(null);
  const [videoToken, setVideoToken] = useState<VideoToken | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [connected, setConnected] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  // Загрузка данных занятия
  useEffect(() => {
    loadSession();
  }, [id]);

  // Таймер занятия
  useEffect(() => {
    if (!connected) return;
    const timer = setInterval(() => setElapsed((prev) => prev + 1), 1000);
    return () => clearInterval(timer);
  }, [connected]);

  const loadSession = async () => {
    try {
      const res = await api.get(`/sessions/${id}`);
      setSession(res.data);
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить данные занятия");
    } finally {
      setLoading(false);
    }
  };

  // Подключение к видеозвонку
  const joinCall = async () => {
    setConnecting(true);
    try {
      const res = await api.post("/video/token", { session_id: Number(id) });
      setVideoToken(res.data);
      setConnected(true);

      // В полной версии здесь инициализируется Agora RTC SDK:
      // const engine = createAgoraRtcEngine();
      // engine.initialize({ appId: res.data.app_id });
      // engine.joinChannel(res.data.token, res.data.channel_name, res.data.uid);
    } catch (e: any) {
      const msg = e.response?.data?.detail || "Не удалось подключиться";
      Alert.alert("Ошибка", msg);
    } finally {
      setConnecting(false);
    }
  };

  // Завершение звонка
  const leaveCall = () => {
    Alert.alert("Завершить занятие", "Вы уверены?", [
      { text: "Отмена", style: "cancel" },
      {
        text: "Завершить",
        style: "destructive",
        onPress: () => {
          setConnected(false);
          setVideoToken(null);
          router.back();
        },
      },
    ]);
  };

  // Форматирование времени
  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
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

  // Экран активного звонка
  if (connected) {
    return (
      <View style={styles.callContainer}>
        {/* Область видео — заглушка для MVP */}
        <View style={styles.videoArea}>
          <View style={styles.remoteVideo}>
            <Text style={styles.videoPlaceholder}>
              {session.tutor_name}
            </Text>
            <Text style={styles.videoSubtext}>Видео репетитора</Text>
          </View>
          <View style={styles.localVideo}>
            <Text style={styles.localVideoText}>Вы</Text>
          </View>
        </View>

        {/* Информация о занятии */}
        <View style={styles.callInfo}>
          <Text style={styles.callSubject}>{session.subject_name}</Text>
          <Text style={styles.callTimer}>{formatTime(elapsed)}</Text>
        </View>

        {/* Кнопки управления */}
        <View style={styles.callControls}>
          <TouchableOpacity style={styles.controlButton}>
            <Text style={styles.controlIcon}>🎤</Text>
            <Text style={styles.controlLabel}>Микрофон</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.controlButton}>
            <Text style={styles.controlIcon}>📷</Text>
            <Text style={styles.controlLabel}>Камера</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.controlButton}>
            <Text style={styles.controlIcon}>💬</Text>
            <Text style={styles.controlLabel}>Чат</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.controlButton, styles.endCallButton]}
            onPress={leaveCall}
          >
            <Text style={styles.controlIcon}>📞</Text>
            <Text style={[styles.controlLabel, { color: "#fff" }]}>Завершить</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Экран ожидания — до подключения
  return (
    <View style={styles.container}>
      <View style={styles.sessionInfo}>
        <View style={styles.sessionAvatar}>
          <Text style={styles.sessionAvatarText}>
            {session.tutor_name.split(" ").map((n) => n[0]).join("")}
          </Text>
        </View>
        <Text style={styles.sessionTutor}>{session.tutor_name}</Text>
        <Text style={styles.sessionSubject}>{session.subject_name}</Text>
        <Text style={styles.sessionDate}>{formatDate(session.scheduled_at)}</Text>
        <Text style={styles.sessionDuration}>
          {session.duration_minutes} минут
        </Text>

        <View style={[styles.statusBadge, session.status === "confirmed" && styles.statusConfirmed]}>
          <Text style={styles.statusText}>
            {session.status === "pending" ? "Ожидает подтверждения" :
             session.status === "confirmed" ? "Подтверждено" :
             session.status === "completed" ? "Завершено" : "Отменено"}
          </Text>
        </View>
      </View>

      {(session.status === "pending" || session.status === "confirmed") && (
        <TouchableOpacity
          style={styles.joinButton}
          onPress={joinCall}
          disabled={connecting}
        >
          {connecting ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.joinButtonText}>Подключиться к занятию</Text>
          )}
        </TouchableOpacity>
      )}

      <TouchableOpacity
        style={styles.cancelButton}
        onPress={() => router.back()}
      >
        <Text style={styles.cancelButtonText}>Назад</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  centered: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.background },
  errorText: { fontSize: 16, color: Colors.textSecondary, marginBottom: 16 },
  backButton: { padding: 12, borderRadius: 8, backgroundColor: Colors.primary },
  backButtonText: { color: "#fff", fontSize: 14, fontWeight: "600" },

  // Экран ожидания
  container: { flex: 1, backgroundColor: Colors.background, padding: 24 },
  sessionInfo: { alignItems: "center", paddingTop: 40 },
  sessionAvatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 16,
  },
  sessionAvatarText: { color: "#fff", fontSize: 32, fontWeight: "700" },
  sessionTutor: { fontSize: 22, fontWeight: "700", color: Colors.text },
  sessionSubject: { fontSize: 16, color: Colors.primary, fontWeight: "600", marginTop: 4 },
  sessionDate: { fontSize: 14, color: Colors.textSecondary, marginTop: 8 },
  sessionDuration: { fontSize: 14, color: Colors.textSecondary, marginTop: 2 },
  statusBadge: {
    marginTop: 16,
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: Colors.warning + "20",
  },
  statusConfirmed: { backgroundColor: Colors.success + "20" },
  statusText: { fontSize: 13, fontWeight: "600", color: Colors.text },

  joinButton: {
    backgroundColor: Colors.secondary,
    borderRadius: 12,
    padding: 18,
    alignItems: "center",
    marginTop: 40,
  },
  joinButtonText: { color: "#fff", fontSize: 17, fontWeight: "700" },
  cancelButton: {
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginTop: 12,
  },
  cancelButtonText: { color: Colors.textSecondary, fontSize: 15 },

  // Экран активного звонка
  callContainer: { flex: 1, backgroundColor: "#1a1a2e" },
  videoArea: { flex: 1, position: "relative" },
  remoteVideo: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#16213e",
  },
  videoPlaceholder: { color: "#fff", fontSize: 24, fontWeight: "700" },
  videoSubtext: { color: "rgba(255,255,255,0.5)", fontSize: 13, marginTop: 4 },
  localVideo: {
    position: "absolute",
    top: 16,
    right: 16,
    width: 100,
    height: 140,
    borderRadius: 12,
    backgroundColor: "#0f3460",
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.3)",
  },
  localVideoText: { color: "#fff", fontSize: 14 },

  callInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: "#16213e",
  },
  callSubject: { color: "#fff", fontSize: 15, fontWeight: "600" },
  callTimer: { color: Colors.secondary, fontSize: 16, fontWeight: "700" },

  callControls: {
    flexDirection: "row",
    justifyContent: "space-around",
    paddingVertical: 20,
    paddingHorizontal: 16,
    backgroundColor: "#16213e",
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.1)",
  },
  controlButton: { alignItems: "center", padding: 8 },
  controlIcon: { fontSize: 24, marginBottom: 4 },
  controlLabel: { color: "rgba(255,255,255,0.7)", fontSize: 11 },
  endCallButton: {
    backgroundColor: Colors.error,
    borderRadius: 12,
    paddingHorizontal: 16,
  },
});
