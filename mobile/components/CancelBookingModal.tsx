// Модалка отмены занятия — за <24ч причина обязательна
import { useMemo, useState } from "react";
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { Colors } from "../constants/theme";

type Props = {
  visible: boolean;
  scheduledAt: string;
  subjectName: string;
  tutorName: string;
  onConfirm: (reason: string) => Promise<void>;
  onClose: () => void;
};

export function CancelBookingModal({
  visible,
  scheduledAt,
  subjectName,
  tutorName,
  onConfirm,
  onClose,
}: Props) {
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Осталось часов до начала занятия
  const hoursLeft = useMemo(() => {
    const diff = new Date(scheduledAt).getTime() - Date.now();
    return diff / (1000 * 60 * 60);
  }, [scheduledAt]);

  const lessThan24h = hoursLeft < 24;
  const reasonRequired = lessThan24h;
  const reasonTooShort = reasonRequired && reason.trim().length < 5;
  const alreadyStarted = hoursLeft <= 0;

  const handleConfirm = async () => {
    if (alreadyStarted || reasonTooShort) return;
    setSubmitting(true);
    try {
      await onConfirm(reason.trim());
      setReason("");
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (submitting) return;
    setReason("");
    onClose();
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
    >
      <KeyboardAvoidingView
        style={styles.backdrop}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <View style={styles.card}>
          <Text style={styles.title}>Отменить занятие?</Text>
          <Text style={styles.subtitle}>
            {subjectName} с {tutorName}
          </Text>

          {alreadyStarted ? (
            <Text style={styles.errorNote}>
              Занятие уже началось — отменить нельзя.
            </Text>
          ) : lessThan24h ? (
            <Text style={styles.warnNote}>
              До начала осталось менее 24 часов. Укажите причину отмены
              (минимум 5 символов).
            </Text>
          ) : (
            <Text style={styles.infoNote}>
              До занятия более 24 часов. Причина необязательна.
            </Text>
          )}

          {!alreadyStarted && (
            <TextInput
              style={styles.input}
              placeholder={reasonRequired ? "Причина отмены" : "Причина (необязательно)"}
              placeholderTextColor={Colors.textSecondary}
              value={reason}
              onChangeText={setReason}
              multiline
              maxLength={500}
              autoFocus
            />
          )}

          <View style={styles.actions}>
            <TouchableOpacity
              style={[styles.btn, styles.btnGhost]}
              onPress={handleClose}
              disabled={submitting}
            >
              <Text style={styles.btnGhostText}>Назад</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.btn,
                styles.btnDanger,
                (alreadyStarted || reasonTooShort || submitting) && styles.btnDisabled,
              ]}
              onPress={handleConfirm}
              disabled={alreadyStarted || reasonTooShort || submitting}
            >
              {submitting ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.btnDangerText}>Отменить занятие</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  card: {
    width: "100%",
    maxWidth: 440,
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 12,
  },
  errorNote: {
    fontSize: 13,
    color: Colors.error,
    backgroundColor: Colors.error + "15",
    padding: 10,
    borderRadius: 10,
    marginBottom: 12,
    lineHeight: 18,
  },
  warnNote: {
    fontSize: 13,
    color: Colors.warning,
    backgroundColor: Colors.warning + "15",
    padding: 10,
    borderRadius: 10,
    marginBottom: 12,
    lineHeight: 18,
  },
  infoNote: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginBottom: 12,
  },
  input: {
    backgroundColor: Colors.inputBg,
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    color: Colors.text,
    minHeight: 80,
    textAlignVertical: "top",
    marginBottom: 16,
  },
  actions: {
    flexDirection: "row",
    gap: 10,
  },
  btn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  btnGhost: {
    backgroundColor: Colors.inputBg,
  },
  btnGhostText: {
    color: Colors.text,
    fontSize: 14,
    fontWeight: "600",
  },
  btnDanger: {
    backgroundColor: Colors.error,
  },
  btnDangerText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "700",
  },
  btnDisabled: {
    opacity: 0.5,
  },
});
