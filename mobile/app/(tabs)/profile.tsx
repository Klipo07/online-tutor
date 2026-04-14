// Экран профиля — меню, переходы в настройки / прогресс / занятия
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from "react-native";
import { useRouter } from "expo-router";
import { useAuthStore } from "../../store/authStore";
import { Colors } from "../../constants/theme";
import { Avatar } from "../../components/Avatar";

export default function ProfileScreen() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    Alert.alert("Выход", "Вы уверены, что хотите выйти?", [
      { text: "Отмена", style: "cancel" },
      { text: "Выйти", style: "destructive", onPress: logout },
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatarWrap}>
          <Avatar name={user?.full_name || "?"} url={user?.avatar_url} size={72} fontSize={24} />
        </View>
        <Text style={styles.name}>{user?.full_name}</Text>
        <Text style={styles.email}>{user?.email}</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>
            {user?.role === "student" ? "Ученик" : user?.role === "tutor" ? "Репетитор" : user?.role}
          </Text>
        </View>
      </View>

      <View style={styles.section}>
        <TouchableOpacity style={styles.menuItem} onPress={() => router.push("/progress")}>
          <Text style={styles.menuIcon}>📊</Text>
          <Text style={styles.menuText}>Мой прогресс</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem} onPress={() => router.push("/my-sessions")}>
          <Text style={styles.menuIcon}>📅</Text>
          <Text style={styles.menuText}>Мои занятия</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem} onPress={() => router.push("/settings")}>
          <Text style={styles.menuIcon}>⚙️</Text>
          <Text style={styles.menuText}>Настройки</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.menuItem} onPress={() => router.push("/help")}>
          <Text style={styles.menuIcon}>❓</Text>
          <Text style={styles.menuText}>Помощь</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Выйти из аккаунта</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: {
    alignItems: "center",
    paddingVertical: 32,
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  avatarWrap: { marginBottom: 12 },
  name: { fontSize: 20, fontWeight: "700", color: Colors.text },
  email: { fontSize: 14, color: Colors.textSecondary, marginTop: 4 },
  badge: {
    backgroundColor: Colors.primary + "20",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 8,
  },
  badgeText: { color: Colors.primary, fontSize: 12, fontWeight: "600" },
  section: { marginTop: 16 },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  menuIcon: { fontSize: 20, marginRight: 12 },
  menuText: { fontSize: 16, color: Colors.text },
  logoutButton: {
    margin: 24,
    padding: 16,
    borderRadius: 12,
    backgroundColor: Colors.error + "10",
    alignItems: "center",
  },
  logoutText: { color: Colors.error, fontSize: 16, fontWeight: "600" },
});
