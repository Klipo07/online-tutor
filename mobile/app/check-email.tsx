// Экран «Проверьте почту» — после регистрации, с кнопкой повторной отправки
import { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import api from "../services/api";
import { Colors } from "../constants/theme";
import { useAuthStore } from "../store/authStore";

const RESEND_COOLDOWN = 60;

export default function CheckEmailScreen() {
  const router = useRouter();
  const { user, checkAuth } = useAuthStore();
  const [cooldown, setCooldown] = useState(RESEND_COOLDOWN);
  const [sending, setSending] = useState(false);

  // Тик секунд cooldown
  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  // Периодически проверяем — вдруг пользователь подтвердил email по ссылке
  useEffect(() => {
    const interval = setInterval(() => {
      checkAuth();
    }, 5000);
    return () => clearInterval(interval);
  }, [checkAuth]);

  useEffect(() => {
    if (user?.email_verified) {
      router.replace("/(tabs)");
    }
  }, [user?.email_verified, router]);

  const resend = async () => {
    if (sending || cooldown > 0) return;
    setSending(true);
    try {
      await api.post("/auth/send-verification");
      setCooldown(RESEND_COOLDOWN);
      Alert.alert("Готово", "Письмо отправлено ещё раз. Проверьте почту.");
    } catch (e: any) {
      const status = e?.response?.status;
      if (status === 429) {
        const retry = parseInt(
          e.response?.headers?.["retry-after"] ?? "60",
          10
        );
        setCooldown(retry);
        Alert.alert(
          "Подождите",
          `Можно запросить снова через ${retry} секунд.`
        );
      } else if (status === 409) {
        Alert.alert("Уже подтверждено", "Email уже подтверждён.");
        checkAuth();
      } else {
        Alert.alert("Ошибка", "Не удалось отправить письмо");
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <Stack.Screen options={{ title: "Подтверждение email" }} />
      <View style={styles.container}>
        <Text style={styles.emoji}>📬</Text>
        <Text style={styles.title}>Проверьте почту</Text>
        <Text style={styles.text}>
          Мы отправили письмо с подтверждением на{" "}
          <Text style={styles.email}>{user?.email}</Text>.
        </Text>
        <Text style={styles.hint}>
          Откройте письмо и нажмите на кнопку «Подтвердить email» — приложение
          откроется автоматически.
        </Text>

        <TouchableOpacity
          style={[
            styles.btn,
            (sending || cooldown > 0) && styles.btnDisabled,
          ]}
          onPress={resend}
          disabled={sending || cooldown > 0}
        >
          {sending ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.btnText}>
              {cooldown > 0 ? `Отправить снова (${cooldown})` : "Отправить снова"}
            </Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.ghost}
          onPress={() => router.replace("/(tabs)")}
        >
          <Text style={styles.ghostText}>Пропустить — подтвердить позже</Text>
        </TouchableOpacity>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    alignItems: "center",
    padding: 24,
    paddingTop: 60,
  },
  emoji: { fontSize: 72, marginBottom: 12 },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 12,
  },
  text: {
    fontSize: 15,
    color: Colors.text,
    textAlign: "center",
    marginBottom: 8,
    lineHeight: 22,
  },
  email: { fontWeight: "700", color: Colors.primary },
  hint: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: "center",
    lineHeight: 20,
    marginBottom: 28,
  },
  btn: {
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
    minWidth: 240,
    alignItems: "center",
  },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: "#fff", fontWeight: "700", fontSize: 15 },
  ghost: { marginTop: 16, padding: 10 },
  ghostText: {
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: "600",
  },
});
