import { View, Text, TextInput, StyleSheet, TextInputProps, Pressable } from 'react-native';
import { colors, borderRadius, fontSize, spacing, touchTarget } from '../theme/tokens';

interface Props extends TextInputProps {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  onIconPress?: () => void;
}

export function Input({ label, error, icon, onIconPress, style, ...props }: Props) {
  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <View style={[styles.inputWrapper, error && styles.inputError]}>
        <TextInput
          style={[styles.input, style]}
          placeholderTextColor={colors.textMuted}
          {...props}
        />
        {icon && (
          <Pressable onPress={onIconPress} style={styles.iconBtn} hitSlop={12}>
            {icon}
          </Pressable>
        )}
      </View>
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: spacing.xs },
  label: { fontSize: fontSize.sm, fontWeight: '600', color: colors.text, marginLeft: spacing.xs },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surface,
    minHeight: touchTarget.min,
  },
  inputError: { borderColor: colors.error },
  input: {
    flex: 1,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    fontSize: fontSize.md,
    color: colors.text,
  },
  iconBtn: { paddingRight: spacing.lg },
  error: { fontSize: fontSize.xs, color: colors.error, marginLeft: spacing.xs },
});
