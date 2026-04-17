// Отзывы о текущем репетиторе
import { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
} from "react-native";
import { Stack } from "expo-router";
import api from "../services/api";
import { Colors } from "../constants/theme";

type Review = {
  id: number;
  student_name: string;
  rating: number;
  comment: string;
};

export default function TutorReviewsScreen() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Review[]>("/tutors/me/reviews")
      .then((res) => setReviews(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Stack.Screen options={{ title: "Отзывы обо мне" }} />
      <View style={styles.container}>
        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={Colors.primary} />
          </View>
        ) : reviews.length === 0 ? (
          <View style={styles.center}>
            <Text style={styles.emptyIcon}>⭐</Text>
            <Text style={styles.emptyTitle}>Пока нет отзывов</Text>
            <Text style={styles.emptySub}>
              После проведённых занятий ученики смогут оставить отзыв
            </Text>
          </View>
        ) : (
          <FlatList
            data={reviews}
            keyExtractor={(r) => String(r.id)}
            contentContainerStyle={styles.list}
            renderItem={({ item }) => (
              <View style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.author}>{item.student_name}</Text>
                  <Text style={styles.rating}>{"\u2B50"} {item.rating}</Text>
                </View>
                <Text style={styles.comment}>{item.comment}</Text>
              </View>
            )}
          />
        )}
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  center: { flex: 1, justifyContent: "center", alignItems: "center", padding: 32 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 17, fontWeight: "700", color: Colors.text },
  emptySub: { fontSize: 14, color: Colors.textSecondary, textAlign: "center", marginTop: 6 },

  list: { padding: 16 },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", marginBottom: 6 },
  author: { fontSize: 14, fontWeight: "600", color: Colors.text },
  rating: { fontSize: 13, color: "#FFB84D" },
  comment: { fontSize: 13, color: Colors.text, lineHeight: 20 },
});
