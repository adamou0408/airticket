/**
 * Trips list screen — placeholder for Phase 2 frontend.
 */
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, fontSize, spacing } from '../../src/theme/tokens';
import { Button } from '../../src/components/Button';

export default function TripsScreen() {
  return (
    <View style={styles.container}>
      <Ionicons name="map-outline" size={64} color={colors.textMuted} />
      <Text style={styles.title}>我的旅程</Text>
      <Text style={styles.subtitle}>建立旅遊計畫、邀請旅伴、共同編輯行程</Text>
      <Button title="+ 建立新旅程" onPress={() => {}} size="lg" />
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
});
