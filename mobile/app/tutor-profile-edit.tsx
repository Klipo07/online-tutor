// Редактирование tutor-специфичных полей: предметы, цена, опыт, образование
import { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import api from "../services/api";
import { Colors } from "../constants/theme";

type TutorProfile = {
  id: number;
  subjects: string[];
  price_per_hour: number;
  experience_years: number;
  education: string | null;
};

type SubjectRef = { id: number; name: string };

export default function TutorProfileEditScreen() {
  const router = useRouter();
  const [catalog, setCatalog] = useState<SubjectRef[]>([]);
  const [subjects, setSubjects] = useState<string[]>([]);
  const [price, setPrice] = useState("");
  const [years, setYears] = useState("");
  const [education, setEducation] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      // Текущий пользователь — чтобы найти свой tutor profile
      const [meRes, subjRes] = await Promise.all([
        api.get<any>("/users/me"),
        api.get<SubjectRef[]>("/subjects"),
      ]);
      setCatalog(subjRes.data);

      // Ищем себя в /tutors по полному имени или используем /tutors/me/stats
      // Проще — читаем свой профиль напрямую из /tutors (перебор) или через me/profile
      // Но у нас нет /tutors/me — используем stats и поиск. Делаем по-простому:
      const meProfile = await api.get<TutorProfile[]>("/tutors", {
        params: { per_page: 50 },
      });
      const my = (meProfile.data as any).tutors.find(
        (t: any) => t.user_id === meRes.data.id
      );
      if (my) {
        setSubjects(my.subjects || []);
        setPrice(String(my.price_per_hour ?? ""));
        setYears(String(my.experience_years ?? ""));
        setEducation(my.education ?? "");
      }
    } catch {
      Alert.alert("Ошибка", "Не удалось загрузить профиль");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const toggleSubject = (name: string) => {
    setSubjects((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]
    );
  };

  const save = async () => {
    const priceNum = Number(price.replace(",", "."));
    const yearsNum = Number(years);
    if (subjects.length === 0) {
      Alert.alert("Ошибка", "Выберите хотя бы один предмет");
      return;
    }
    if (!(priceNum > 0)) {
      Alert.alert("Ошибка", "Укажите цену за час");
      return;
    }
    if (!(yearsNum >= 0)) {
      Alert.alert("Ошибка", "Укажите опыт в годах");
      return;
    }

    setSaving(true);
    try {
      await api.patch("/tutors/me/profile", {
        subjects,
        price_per_hour: priceNum,
        experience_years: yearsNum,
        education: education.trim() || null,
      });
      Alert.alert("Сохранено", "Профиль обновлён", [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch (e: any) {
      const msg = e?.response?.data?.detail || "Не удалось сохранить";
      Alert.alert("Ошибка", typeof msg === "string" ? msg : "Проверьте поля");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: "Мой профиль" }} />
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.sectionTitle}>Предметы</Text>
        <Text style={styles.hint}>Выберите предметы, которые преподаёте</Text>
        <View style={styles.chipsRow}>
          {catalog.map((s) => {
            const active = subjects.includes(s.name);
            return (
              <TouchableOpacity
                key={s.id}
                style={[styles.chip, active && styles.chipActive]}
                onPress={() => toggleSubject(s.name)}
              >
                <Text style={[styles.chipText, active && styles.chipTextActive]}>
                  {s.name}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <Text style={styles.sectionTitle}>Цена за час, ₽</Text>
        <TextInput
          style={styles.input}
          value={price}
          onChangeText={setPrice}
          keyboardType="numeric"
          placeholder="1500"
          placeholderTextColor={Colors.textSecondary}
        />

        <Text style={styles.sectionTitle}>Опыт преподавания, лет</Text>
        <TextInput
          style={styles.input}
          value={years}
          onChangeText={setYears}
          keyboardType="numeric"
          placeholder="5"
          placeholderTextColor={Colors.textSecondary}
        />

        <Text style={styles.sectionTitle}>Образование</Text>
        <TextInput
          style={[styles.input, styles.multiline]}
          value={education}
          onChangeText={setEducation}
          placeholder="МГУ, физический факультет, 2015"
          placeholderTextColor={Colors.textSecondary}
          multiline
          maxLength={500}
        />

        <TouchableOpacity
          style={[styles.saveBtn, saving && { opacity: 0.5 }]}
          onPress={save}
          disabled={saving}
        >
          <Text style={styles.saveBtnText}>
            {saving ? "Сохранение..." : "Сохранить изменения"}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 40 },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.background },
  sectionTitle: { fontSize: 15, fontWeight: "700", color: Colors.text, marginTop: 20, marginBottom: 6 },
  hint: { fontSize: 12, color: Colors.textSecondary, marginBottom: 10 },
  chipsRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    backgroundColor: Colors.inputBg,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  chipText: { color: Colors.text, fontSize: 13, fontWeight: "500" },
  chipTextActive: { color: "#fff" },
  input: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  multiline: { minHeight: 80, textAlignVertical: "top" },
  saveBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginTop: 24,
  },
  saveBtnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
});
