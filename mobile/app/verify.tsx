// Обработка deep link подтверждения email: ai-tutor://verify?token=...
import { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from "react-native";
import { useLocalSearchParams, useRouter, Stack } from "expo-router";
import api from "../services/api";
import { Colors } from "../constants/theme";
import { useAuthStore } from "../store/authStore";

type Stage = "loading" | "success" | "expired" | "invalid" | "error";

export default function VerifyScreen() {
  const { token } = useLocalSearchParams<{ token?: string }>();
  const router = useRouter();
  const { checkAuth } = useAuthStore();
  const [stage, setStage] = useState<Stage>("loading");

  useEffect(() => {
    if (!token) {
      setStage("invalid");
      return;
    }
    (async () => {
      try {
        await api.get(`/auth/verify-email`, { params: { token } });
        setStage("success");
        // Обновим данные пользователя, чтобы убрать баннер
        checkAuth();
      } catch (e: any) {
        const status = e?.response?.status;
        if (status === 410) setStage("expired");
        else if (status === 404) setStage("invalid");
        else setStage("error");
      }
    })();
  }, [token]);

  return (
    <>
      <Stack.Screen options={{ title: "Подтверждение email" }} />
      <View style={styles.container}>
        {stage === "loading" && (
          <>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.text}>Подтверждаем email…</Text>
          </>
        )}
        {stage === "success" && (
          <>
            <Text style={styles.emoji}>✅</Text>
            <Text style={styles.title}>Email подтверждён</Text>
            <Text style={styles.text}>
              Теперь вам доступны все функции AI Tutor.
            </Text>
            <TouchableOpacity
              style={styles.btn}
              onPress={() => router.replace("/(tabs)")}
            >
              <Text style={styles.btnText}>Перейти в приложение</Text>
            </TouchableOpacity>
          </>
        )}
        {stage === "expired" && (
          <>
            <Text style={styles.emoji}>⏰</Text>
            <Text style={styles.title}>Ссылка устарела</Text>
            <Text style={styles.text}>
              Срок действия ссылки истёк. Запросите новое письмо в настройках
              профиля.
            </Text>
            <TouchableOpacity
              style={styles.btn}
              onPress={() => router.replace("/settings")}
            >
              <Text style={styles.btnText}>Открыть настройки</Text>
            </TouchableOpacity>
          </>
        )}
        {stage === "invalid" && (
          <>
            <Text style={styles.emoji}>❌</Text>
            <Text style={styles.title}>Ссылка недействительна</Text>
            <Text style={styles.text}>
              Токен уже использован или неправильный. Попробуйте запросить новое
              письмо.
            </Text>
            <TouchableOpacity
              style={styles.btn}
              onPress={() => router.replace("/settings")}
            >
              <Text style={styles.btnText}>Открыть настройки</Text>
            </TouchableOpacity>
          </>
        )}
        {stage === "error" && (
          <>
            <Text style={styles.emoji}>⚠️</Text>
            <Text style={styles.title}>Что-то пошло не так</Text>
            <Text style={styles.text}>
              Не удалось подтвердить email. Проверьте соединение и попробуйте
              снова.
            </Text>
            <TouchableOpacity
              style={styles.btn}
              onPress={() => router.replace("/(tabs)")}
            >
              <Text style={styles.btnText}>Продолжить</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  emoji: { fontSize: 72, marginBottom: 12 },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 8,
    textAlign: "center",
  },
  text: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: "center",
    marginTop: 8,
    marginBottom: 24,
    lineHeight: 22,
  },
  btn: {
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
  },
  btnText: { color: "#fff", fontWeight: "700", fontSize: 15 },
});
