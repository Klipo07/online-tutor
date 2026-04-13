// Индикатор силы пароля + чек-лист требований
import { View, Text, StyleSheet } from "react-native";
import { Colors } from "../constants/theme";

export type PasswordChecks = {
  length: boolean;
  letter: boolean;
  uppercase: boolean;
  digit: boolean;
  special: boolean;
};

export function checkPassword(password: string): PasswordChecks {
  return {
    length: password.length >= 6,
    letter: /[A-Za-zА-Яа-яЁё]/.test(password),
    uppercase: /[A-ZА-ЯЁ]/.test(password),
    digit: /\d/.test(password),
    special: /[^A-Za-zА-Яа-яЁё0-9]/.test(password),
  };
}

function strengthScore(checks: PasswordChecks): number {
  return Object.values(checks).filter(Boolean).length;
}

const LABELS = ["Очень слабый", "Слабый", "Средний", "Сильный", "Очень сильный"];
const BAR_COLORS = ["#e5e7eb", "#ef4444", "#f59e0b", "#eab308", "#22c55e", "#16a34a"];

type Props = {
  password: string;
  showChecklist?: boolean;
};

export default function PasswordStrengthIndicator({ password, showChecklist = true }: Props) {
  if (!password) return null;

  const checks = checkPassword(password);
  const score = strengthScore(checks);
  const label = LABELS[Math.max(0, score - 1)];
  const color = BAR_COLORS[score];

  return (
    <View style={styles.wrap}>
      <View style={styles.bars}>
        {[0, 1, 2, 3, 4].map((i) => (
          <View
            key={i}
            style={[
              styles.bar,
              { backgroundColor: i < score ? color : Colors.inputBg },
            ]}
          />
        ))}
      </View>
      <Text style={[styles.label, { color }]}>{label}</Text>

      {showChecklist && (
        <View style={styles.checklist}>
          <Rule ok={checks.length} text="Минимум 6 символов" />
          <Rule ok={checks.letter} text="Хотя бы одна буква" />
          <Rule ok={checks.uppercase} text="Хотя бы одна заглавная" />
          <Rule ok={checks.digit} text="Хотя бы одна цифра (желательно)" />
        </View>
      )}
    </View>
  );
}

function Rule({ ok, text }: { ok: boolean; text: string }) {
  return (
    <Text style={[styles.rule, { color: ok ? "#16a34a" : Colors.textSecondary }]}>
      {ok ? "✓" : "○"} {text}
    </Text>
  );
}

/** Пароль проходит серверную валидацию: длина, буква, заглавная. */
export function isPasswordValid(password: string): boolean {
  const c = checkPassword(password);
  return c.length && c.letter && c.uppercase;
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: 12,
  },
  bars: {
    flexDirection: "row",
    gap: 4,
    marginBottom: 6,
  },
  bar: {
    flex: 1,
    height: 4,
    borderRadius: 2,
  },
  label: {
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 8,
  },
  checklist: {
    gap: 2,
  },
  rule: {
    fontSize: 12,
  },
});
