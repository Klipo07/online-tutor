// Экран настроек аккаунта — профиль, аватар, смена пароля
import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import { KeyboardAwareScrollView } from "react-native-keyboard-controller";
import { Avatar } from "../components/Avatar";
import api from "../services/api";
import { useAuthStore } from "../store/authStore";
import { Colors } from "../constants/theme";

export default function SettingsScreen() {
  const router = useRouter();
  const { user, setUser, logout } = useAuthStore();

  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [bio, setBio] = useState(user?.bio ?? "");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Смена пароля
  const [oldPass, setOldPass] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirmPass, setConfirmPass] = useState("");
  const [changingPass, setChangingPass] = useState(false);

  const pickAvatar = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      Alert.alert("Нет доступа", "Разрешите доступ к галерее в настройках");
      return;
    }
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });
    if (res.canceled) return;

    const asset = res.assets[0];
    setUploading(true);
    try {
      const form = new FormData();
      const uri = asset.uri;
      const extMatch = uri.match(/\.(jpe?g|png|webp)$/i);
      const ext = (extMatch?.[1] ?? "jpg").toLowerCase();
      const mime = ext === "png" ? "image/png" : ext === "webp" ? "image/webp" : "image/jpeg";
      // @ts-expect-error FormData file shape for RN
      form.append("file", { uri, name: `avatar.${ext}`, type: mime });

      const resp = await api.post("/users/me/avatar", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUser(resp.data);
    } catch (e: any) {
      Alert.alert("Ошибка", e?.response?.data?.detail ?? "Не удалось загрузить аватар");
    } finally {
      setUploading(false);
    }
  };

  const saveProfile = async () => {
    if (firstName.trim().length < 2 || lastName.trim().length < 2) {
      Alert.alert("Ошибка", "Имя и фамилия должны содержать минимум 2 символа");
      return;
    }
    setSaving(true);
    try {
      const resp = await api.put("/users/me", {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone.trim() || null,
        bio: bio.trim() || null,
      });
      setUser(resp.data);
      Alert.alert("Сохранено", "Профиль обновлён");
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail[0]?.msg : detail;
      Alert.alert("Ошибка", msg ?? "Не удалось сохранить профиль");
    } finally {
      setSaving(false);
    }
  };

  const changePassword = async () => {
    if (!oldPass || !newPass) {
      Alert.alert("Ошибка", "Заполните старый и новый пароль");
      return;
    }
    if (newPass !== confirmPass) {
      Alert.alert("Ошибка", "Пароли не совпадают");
      return;
    }
    setChangingPass(true);
    try {
      await api.post("/users/me/password", {
        old_password: oldPass,
        new_password: newPass,
      });
      setOldPass("");
      setNewPass("");
      setConfirmPass("");
      Alert.alert("Готово", "Пароль изменён");
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail[0]?.msg : detail;
      Alert.alert("Ошибка", msg ?? "Не удалось сменить пароль");
    } finally {
      setChangingPass(false);
    }
  };

  return (
    <>
      <Stack.Screen options={{ title: "Настройки" }} />
      <KeyboardAwareScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        bottomOffset={20}
      >
        {/* Аватар */}
        <View style={styles.avatarSection}>
          <TouchableOpacity onPress={pickAvatar} disabled={uploading}>
            <Avatar name={user?.full_name || "?"} url={user?.avatar_url} size={100} fontSize={34} />
            {uploading && (
              <View style={styles.avatarOverlay}>
                <ActivityIndicator color="#fff" />
              </View>
            )}
          </TouchableOpacity>
          <TouchableOpacity onPress={pickAvatar} disabled={uploading} style={styles.avatarBtn}>
            <Text style={styles.avatarBtnText}>
              {user?.avatar_url ? "Сменить фото" : "Загрузить фото"}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Email (read-only) */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Аккаунт</Text>
          <Text style={styles.label}>Email</Text>
          <View style={styles.readonly}>
            <Text style={styles.readonlyText}>{user?.email}</Text>
          </View>
        </View>

        {/* Профиль */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Профиль</Text>

          <Text style={styles.label}>Имя</Text>
          <TextInput
            style={styles.input}
            value={firstName}
            onChangeText={setFirstName}
            placeholder="Имя"
            placeholderTextColor={Colors.textSecondary}
          />

          <Text style={styles.label}>Фамилия</Text>
          <TextInput
            style={styles.input}
            value={lastName}
            onChangeText={setLastName}
            placeholder="Фамилия"
            placeholderTextColor={Colors.textSecondary}
          />

          <Text style={styles.label}>Телефон</Text>
          <TextInput
            style={styles.input}
            value={phone}
            onChangeText={setPhone}
            placeholder="+7 (___) ___-__-__"
            keyboardType="phone-pad"
            placeholderTextColor={Colors.textSecondary}
          />

          <View style={styles.bioHeader}>
            <Text style={styles.label}>О себе</Text>
            <Text style={styles.bioCount}>{bio.length}/500</Text>
          </View>
          <TextInput
            style={[styles.input, styles.bioInput]}
            value={bio}
            onChangeText={(t) => setBio(t.slice(0, 500))}
            placeholder="Расскажите о себе в нескольких предложениях"
            placeholderTextColor={Colors.textSecondary}
            multiline
            maxLength={500}
          />

          <TouchableOpacity
            style={[styles.saveBtn, saving && styles.disabledBtn]}
            onPress={saveProfile}
            disabled={saving}
          >
            <Text style={styles.saveBtnText}>
              {saving ? "Сохранение..." : "Сохранить изменения"}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Смена пароля */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Смена пароля</Text>

          <Text style={styles.label}>Текущий пароль</Text>
          <TextInput
            style={styles.input}
            value={oldPass}
            onChangeText={setOldPass}
            secureTextEntry
            placeholder="••••••"
            placeholderTextColor={Colors.textSecondary}
          />

          <Text style={styles.label}>Новый пароль</Text>
          <TextInput
            style={styles.input}
            value={newPass}
            onChangeText={setNewPass}
            secureTextEntry
            placeholder="Минимум 6 символов, 1 заглавная"
            placeholderTextColor={Colors.textSecondary}
          />

          <Text style={styles.label}>Подтвердите пароль</Text>
          <TextInput
            style={styles.input}
            value={confirmPass}
            onChangeText={setConfirmPass}
            secureTextEntry
            placeholder="Повторите новый пароль"
            placeholderTextColor={Colors.textSecondary}
          />

          <TouchableOpacity
            style={[styles.saveBtn, changingPass && styles.disabledBtn]}
            onPress={changePassword}
            disabled={changingPass}
          >
            <Text style={styles.saveBtnText}>
              {changingPass ? "Меняем..." : "Сменить пароль"}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Опасная зона */}
        <TouchableOpacity
          style={styles.logoutBtn}
          onPress={() =>
            Alert.alert("Выход", "Вы уверены?", [
              { text: "Отмена", style: "cancel" },
              {
                text: "Выйти",
                style: "destructive",
                onPress: async () => {
                  await logout();
                  router.replace("/(auth)/login");
                },
              },
            ])
          }
        >
          <Text style={styles.logoutBtnText}>Выйти из аккаунта</Text>
        </TouchableOpacity>
      </KeyboardAwareScrollView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 16, paddingBottom: 40 },
  avatarSection: { alignItems: "center", marginBottom: 20 },
  avatarOverlay: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: 50,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "center",
    alignItems: "center",
  },
  avatarBtn: { marginTop: 12, paddingVertical: 6, paddingHorizontal: 14 },
  avatarBtnText: { color: Colors.primary, fontSize: 14, fontWeight: "600" },
  section: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sectionTitle: { fontSize: 17, fontWeight: "700", color: Colors.text, marginBottom: 12 },
  label: { fontSize: 13, color: Colors.textSecondary, marginTop: 10, marginBottom: 6 },
  input: {
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: Colors.text,
  },
  bioHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end" },
  bioCount: { fontSize: 12, color: Colors.textSecondary, marginBottom: 6 },
  bioInput: { minHeight: 90, textAlignVertical: "top" },
  readonly: {
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  readonlyText: { fontSize: 15, color: Colors.textSecondary },
  saveBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 16,
  },
  disabledBtn: { opacity: 0.5 },
  saveBtnText: { color: "#fff", fontSize: 15, fontWeight: "700" },
  logoutBtn: {
    marginTop: 8,
    padding: 16,
    borderRadius: 12,
    backgroundColor: Colors.error + "15",
    alignItems: "center",
  },
  logoutBtnText: { color: Colors.error, fontSize: 15, fontWeight: "600" },
});
