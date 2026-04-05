/**
 * Expenses screen — placeholder for Phase 4 frontend.
 */
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fontSize, spacing } from '../../src/theme/tokens';

export default function ExpensesScreen() {
  return (
    <View style={styles.container}>
      <Ionicons name="wallet-outline" size={64} color={colors.textMuted} />
      <Text style={styles.title}>記帳拆帳</Text>
      <Text style={styles.subtitle}>快速記錄花費、自動拆帳結算</Text>
      <Text style={styles.hint}>請先在「行程」頁面選擇一個旅遊計畫</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1, backgroundColor: colors.background,
    justifyContent: 'center', alignItems: 'center',
    padding: spacing.xxl, gap: spacing.lg,
  },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: fontSize.md, color: colors.textSecondary, textAlign: 'center' },
  hint: { fontSize: fontSize.sm, color: colors.textMuted },
});
