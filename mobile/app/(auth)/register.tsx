// Экран регистрации — для учеников и репетиторов (Segmented Control)
import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import { useAuthStore, type RegisterPayload } from "../../store/authStore";
import { Colors } from "../../constants/theme";
import PasswordStrengthIndicator, {
  isPasswordValid,
} from "../../components/PasswordStrengthIndicator";

// Предметы для чипов в форме регистрации репетитора
const SUBJECT_OPTIONS = [
  "Математика",
  "Русский язык",
  "Физика",
  "Химия",
  "Биология",
  "История",
  "Обществознание",
  "Английский язык",
  "Информатика",
  "География",
  "Литература",
];

type Role = "student" | "tutor";

export default function RegisterScreen() {
  const [role, setRole] = useState<Role>("student");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Поля только для репетитора
  const [subjects, setSubjects] = useState<string[]>([]);
  const [pricePerHour, setPricePerHour] = useState("");
  const [experienceYears, setExperienceYears] = useState("");
  const [bio, setBio] = useState("");
  const [education, setEducation] = useState("");

  const [loading, setLoading] = useState(false);
  const register = useAuthStore((s) => s.register);
  const router = useRouter();

  const toggleSubject = (subject: string) => {
    setSubjects((prev) =>
      prev.includes(subject) ? prev.filter((s) => s !== subject) : [...prev, subject]
    );
  };

  const validateTutorFields = (): string | null => {
    if (subjects.length === 0) return "Выберите хотя бы один предмет";
    const price = Number(pricePerHour);
    if (!pricePerHour || isNaN(price) || price < 0) return "Укажите корректную цену за час";
    const exp = Number(experienceYears);
    if (experienceYears === "" || isNaN(exp) || exp < 0 || exp > 70)
      return "Стаж — число от 0 до 70";
    return null;
  };

  const handleRegister = async () => {
    if (!firstName.trim() || !lastName.trim() || !email || !password) {
      Alert.alert("Ошибка", "Заполните все поля");
      return;
    }
    if (firstName.trim().length < 2 || lastName.trim().length < 2) {
      Alert.alert("Ошибка", "Имя и фамилия — минимум 2 символа");
      return;
    }
    if (!isPasswordValid(password)) {
      Alert.alert(
        "Слабый пароль",
        "Пароль должен содержать минимум 6 символов, включая букву и заглавную букву"
      );
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert("Ошибка", "Пароли не совпадают");
      return;
    }

    let payload: RegisterPayload;
    if (role === "tutor") {
      const err = validateTutorFields();
      if (err) {
        Alert.alert("Ошибка", err);
        return;
      }
      payload = {
        role: "tutor",
        email: email.trim().toLowerCase(),
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        subjects,
        price_per_hour: Number(pricePerHour),
        experience_years: Number(experienceYears),
        bio: bio.trim() || undefined,
        education: education.trim() || undefined,
      };
    } else {
      payload = {
        role: "student",
        email: email.trim().toLowerCase(),
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      };
    }

    setLoading(true);
    try {
      await register(payload);
      // После регистрации — на экран «Проверьте почту»
      router.replace("/check-email");
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      const msg = Array.isArray(detail)
        ? detail.map((d: any) => d.msg).join("\n")
        : detail || "Ошибка регистрации";
      Alert.alert("Ошибка", msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.logo}>AI Tutor</Text>
          <Text style={styles.subtitle}>Создайте аккаунт</Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.title}>Регистрация</Text>

          {/* Segmented Control — ученик / репетитор */}
          <View style={styles.segmented}>
            <TouchableOpacity
              style={[styles.segBtn, role === "student" && styles.segBtnActive]}
              onPress={() => setRole("student")}
            >
              <Text
                style={[styles.segText, role === "student" && styles.segTextActive]}
              >
                Я ученик
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.segBtn, role === "tutor" && styles.segBtnActive]}
              onPress={() => setRole("tutor")}
            >
              <Text
                style={[styles.segText, role === "tutor" && styles.segTextActive]}
              >
                Я репетитор
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.row}>
            <TextInput
              style={[styles.input, styles.inputHalf]}
              placeholder="Имя"
              placeholderTextColor={Colors.textSecondary}
              value={firstName}
              onChangeText={setFirstName}
              autoCapitalize="words"
            />
            <TextInput
              style={[styles.input, styles.inputHalf]}
              placeholder="Фамилия"
              placeholderTextColor={Colors.textSecondary}
              value={lastName}
              onChangeText={setLastName}
              autoCapitalize="words"
            />
          </View>

          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={Colors.textSecondary}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <TextInput
            style={styles.input}
            placeholder="Пароль"
            placeholderTextColor={Colors.textSecondary}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <PasswordStrengthIndicator password={password} />

          <TextInput
            style={styles.input}
            placeholder="Подтвердите пароль"
            placeholderTextColor={Colors.textSecondary}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry
          />

          {/* Блок полей репетитора — показываем только при role=tutor */}
          {role === "tutor" && (
            <View style={styles.tutorBlock}>
              <Text style={styles.sectionLabel}>Ваши предметы</Text>
              <View style={styles.chips}>
                {SUBJECT_OPTIONS.map((s) => {
                  const active = subjects.includes(s);
                  return (
                    <TouchableOpacity
                      key={s}
                      style={[styles.chip, active && styles.chipActive]}
                      onPress={() => toggleSubject(s)}
                    >
                      <Text
                        style={[styles.chipText, active && styles.chipTextActive]}
                      >
                        {s}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              <View style={styles.row}>
                <TextInput
                  style={[styles.input, styles.inputHalf]}
                  placeholder="Цена за час, ₽"
                  placeholderTextColor={Colors.textSecondary}
                  value={pricePerHour}
                  onChangeText={setPricePerHour}
                  keyboardType="numeric"
                />
                <TextInput
                  style={[styles.input, styles.inputHalf]}
                  placeholder="Стаж, лет"
                  placeholderTextColor={Colors.textSecondary}
                  value={experienceYears}
                  onChangeText={setExperienceYears}
                  keyboardType="numeric"
                />
              </View>

              <TextInput
                style={[styles.input, styles.inputMultiline]}
                placeholder="О себе (необязательно)"
                placeholderTextColor={Colors.textSecondary}
                value={bio}
                onChangeText={setBio}
                multiline
                numberOfLines={3}
              />

              <TextInput
                style={styles.input}
                placeholder="Образование (необязательно)"
                placeholderTextColor={Colors.textSecondary}
                value={education}
                onChangeText={setEducation}
              />

              <Text style={styles.hint}>
                После регистрации ваш профиль появится в каталоге после верификации email.
              </Text>
            </View>
          )}

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleRegister}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading ? "Регистрация..." : "Зарегистрироваться"}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => router.back()}>
            <Text style={styles.link}>
              Уже есть аккаунт? <Text style={styles.linkBold}>Войти</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scroll: {
    flexGrow: 1,
    justifyContent: "center",
    padding: 24,
  },
  header: {
    alignItems: "center",
    marginBottom: 40,
  },
  logo: {
    fontSize: 36,
    fontWeight: "800",
    color: Colors.primary,
  },
  subtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginTop: 8,
  },
  form: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 20,
  },
  segmented: {
    flexDirection: "row",
    backgroundColor: Colors.inputBg,
    borderRadius: 12,
    padding: 4,
    marginBottom: 16,
  },
  segBtn: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
    borderRadius: 8,
  },
  segBtnActive: {
    backgroundColor: Colors.primary,
  },
  segText: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.textSecondary,
  },
  segTextActive: {
    color: "#fff",
  },
  row: {
    flexDirection: "row",
    gap: 12,
  },
  input: {
    backgroundColor: Colors.inputBg,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: Colors.text,
    marginBottom: 12,
  },
  inputHalf: {
    flex: 1,
  },
  inputMultiline: {
    minHeight: 80,
    textAlignVertical: "top",
  },
  tutorBlock: {
    marginTop: 4,
    marginBottom: 4,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.textSecondary,
    marginBottom: 10,
    marginTop: 6,
  },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 12,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: Colors.inputBg,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  chipText: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  chipTextActive: {
    color: "#fff",
    fontWeight: "600",
  },
  hint: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 4,
    marginBottom: 8,
    lineHeight: 16,
  },
  button: {
    backgroundColor: Colors.primary,
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  link: {
    textAlign: "center",
    marginTop: 20,
    color: Colors.textSecondary,
    fontSize: 14,
  },
  linkBold: {
    color: Colors.primary,
    fontWeight: "600",
  },
});
