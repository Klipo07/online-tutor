// Переиспользуемый аватар с инициалами
import { memo, useMemo } from "react";
import { View, Text, StyleSheet } from "react-native";
import { Colors } from "../constants/theme";

type Props = {
  name: string;
  size?: number;
  fontSize?: number;
};

function getInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function AvatarComponent({ name, size = 48, fontSize }: Props) {
  const initials = useMemo(() => getInitials(name), [name]);
  const textSize = fontSize ?? Math.round(size / 3);
  return (
    <View
      style={[
        styles.avatar,
        { width: size, height: size, borderRadius: size / 2 },
      ]}
    >
      <Text style={[styles.text, { fontSize: textSize }]}>{initials}</Text>
    </View>
  );
}

export const Avatar = memo(AvatarComponent);

const styles = StyleSheet.create({
  avatar: {
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
  },
  text: { color: "#fff", fontWeight: "700" },
});
