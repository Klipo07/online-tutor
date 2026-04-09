// Экран маркетплейса репетиторов
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { Colors } from "../../constants/theme";

// Заглушка — данные репетиторов (потом будет с API)
const mockTutors = [
  { id: 1, name: "Анна Сергеевна", subject: "Математика", price: 1500, rating: 4.9, experience: 8 },
  { id: 2, name: "Дмитрий Иванов", subject: "Физика", price: 1200, rating: 4.7, experience: 5 },
  { id: 3, name: "Елена Петрова", subject: "Русский язык", price: 1300, rating: 4.8, experience: 12 },
  { id: 4, name: "Михаил Козлов", subject: "Информатика", price: 1800, rating: 5.0, experience: 6 },
  { id: 5, name: "Ольга Новикова", subject: "Английский", price: 1400, rating: 4.6, experience: 10 },
];

export default function TutorsScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Репетиторы</Text>
      <Text style={styles.subtitle}>Найдите своего преподавателя</Text>

      {mockTutors.map((tutor) => (
        <TouchableOpacity key={tutor.id} style={styles.card}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {tutor.name.split(" ").map((n) => n[0]).join("")}
            </Text>
          </View>
          <View style={styles.info}>
            <Text style={styles.name}>{tutor.name}</Text>
            <Text style={styles.subject}>{tutor.subject}</Text>
            <View style={styles.meta}>
              <Text style={styles.rating}>⭐ {tutor.rating}</Text>
              <Text style={styles.experience}>{tutor.experience} лет опыта</Text>
            </View>
          </View>
          <View style={styles.priceBox}>
            <Text style={styles.price}>{tutor.price} ₽</Text>
            <Text style={styles.priceLabel}>/ час</Text>
          </View>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 24 },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text, marginBottom: 4 },
  subtitle: { fontSize: 14, color: Colors.textSecondary, marginBottom: 20 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
  },
  avatarText: { color: "#fff", fontWeight: "700", fontSize: 16 },
  info: { flex: 1, marginLeft: 12 },
  name: { fontSize: 15, fontWeight: "600", color: Colors.text },
  subject: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  meta: { flexDirection: "row", gap: 12, marginTop: 4 },
  rating: { fontSize: 12, color: Colors.warning },
  experience: { fontSize: 12, color: Colors.textSecondary },
  priceBox: { alignItems: "center" },
  price: { fontSize: 16, fontWeight: "700", color: Colors.primary },
  priceLabel: { fontSize: 11, color: Colors.textSecondary },
});
