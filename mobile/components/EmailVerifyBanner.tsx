// Баннер «Email не подтверждён» — показывается в шапке таба/главной
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { useRouter } from "expo-router";
import { Colors } from "../constants/theme";
import { useAuthStore } from "../store/authStore";

export function EmailVerifyBanner() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  // Показываем только если пользователь залогинен и email не подтверждён
  if (!user || user.email_verified) return null;

  return (
    <TouchableOpacity
      style={styles.banner}
      onPress={() => router.push("/check-email")}
      activeOpacity={0.85}
    >
      <Text style={styles.icon}>📧</Text>
      <View style={{ flex: 1 }}>
        <Text style={styles.title}>Email не подтверждён</Text>
        <Text style={styles.text}>
          Подтвердите {user.email}, чтобы активировать все функции
        </Text>
      </View>
      <Text style={styles.chevron}>›</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.warning + "1F",
    borderWidth: 1,
    borderColor: Colors.warning + "55",
    borderRadius: 12,
    padding: 12,
    marginHorizontal: 16,
    marginTop: 12,
    gap: 10,
  },
  icon: { fontSize: 20 },
  title: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.text,
  },
  text: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  chevron: {
    fontSize: 22,
    color: Colors.textSecondary,
    paddingHorizontal: 4,
  },
});
