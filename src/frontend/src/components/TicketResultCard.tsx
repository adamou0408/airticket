/**
 * Outstation ticket result card — shows 4-leg route, price, savings.
 * Mobile-optimized: large text, clear visual hierarchy.
 */
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, borderRadius, fontSize, spacing } from '../theme/tokens';
import { Card } from './Card';
import type { OutstationTicket } from '../api/tickets';

interface Props {
  ticket: OutstationTicket;
  passengers: number;
  onPress?: () => void;
}

export function TicketResultCard({ ticket, passengers, onPress }: Props) {
  const hasSavings = ticket.savings != null && ticket.savings > 0;

  return (
    <Pressable onPress={onPress}>
      <Card style={styles.card}>
        {/* Header: outstation city + savings badge */}
        <View style={styles.header}>
          <View style={styles.outstationBadge}>
            <Ionicons name="airplane" size={14} color={colors.primary} />
            <Text style={styles.outstationText}>
              外站：{ticket.outstation_city_name} ({ticket.outstation_city})
            </Text>
          </View>
          {hasSavings && (
            <View style={styles.savingsBadge}>
              <Text style={styles.savingsText}>
                省 {ticket.savings_percent}%
              </Text>
            </View>
          )}
        </View>

        {/* 4-leg route visualization */}
        <View style={styles.route}>
          {ticket.legs.map((leg, i) => (
            <View key={i} style={styles.legRow}>
              <View style={[styles.legDot, i === 0 || i === 3 ? styles.dotOutstation : styles.dotNormal]} />
              <Text style={styles.legText}>
                {leg.origin} → {leg.destination}
              </Text>
              <Text style={styles.legAirline}>{leg.airline}</Text>
              <Text style={styles.legPrice}>${leg.price.toLocaleString()}</Text>
            </View>
          ))}
        </View>

        {/* Footer: total price */}
        <View style={styles.footer}>
          <View>
            <Text style={styles.totalLabel}>
              {passengers > 1 ? `${passengers} 人總價` : '總價'}
            </Text>
            <Text style={styles.totalPrice}>
              {ticket.currency} {ticket.total_price.toLocaleString()}
            </Text>
          </View>
          {hasSavings && ticket.direct_price && (
            <View style={styles.comparison}>
              <Text style={styles.directLabel}>直飛</Text>
              <Text style={styles.directPrice}>
                ${ticket.direct_price.toLocaleString()}
              </Text>
              <Text style={styles.savingsAmount}>
                省 ${ticket.savings!.toLocaleString()}
              </Text>
            </View>
          )}
        </View>
      </Card>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: spacing.md },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  outstationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  outstationText: { fontSize: fontSize.sm, fontWeight: '600', color: colors.primaryDark },
  savingsBadge: {
    backgroundColor: colors.success,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  savingsText: { fontSize: fontSize.sm, fontWeight: '700', color: '#fff' },
  route: { gap: spacing.sm, marginBottom: spacing.lg },
  legRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  legDot: { width: 8, height: 8, borderRadius: 4 },
  dotOutstation: { backgroundColor: colors.primary },
  dotNormal: { backgroundColor: colors.secondary },
  legText: { fontSize: fontSize.sm, color: colors.text, flex: 1 },
  legAirline: { fontSize: fontSize.xs, color: colors.textSecondary },
  legPrice: { fontSize: fontSize.sm, fontWeight: '600', color: colors.text },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    paddingTop: spacing.md,
  },
  totalLabel: { fontSize: fontSize.xs, color: colors.textSecondary },
  totalPrice: { fontSize: fontSize.xl, fontWeight: '700', color: colors.primary },
  comparison: { alignItems: 'flex-end' },
  directLabel: { fontSize: fontSize.xs, color: colors.textMuted },
  directPrice: { fontSize: fontSize.sm, color: colors.textMuted, textDecorationLine: 'line-through' },
  savingsAmount: { fontSize: fontSize.sm, fontWeight: '600', color: colors.success },
});
