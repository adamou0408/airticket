/**
 * Design tokens — mobile-first, thumb-friendly.
 * Large touch targets (48px+), clear visual hierarchy, warm travel theme.
 */

export const colors = {
  primary: '#FF6B35',     // 活力橘 — 旅遊的熱情
  primaryLight: '#FFE8DD',
  primaryDark: '#D4562A',
  secondary: '#004E89',   // 深藍 — 天空/海洋
  secondaryLight: '#E3F0FF',
  accent: '#2EC4B6',      // 薄荷綠 — 清爽
  accentLight: '#E0F7F5',

  background: '#FAFAFA',
  surface: '#FFFFFF',
  surfaceElevated: '#FFFFFF',

  text: '#1A1A2E',
  textSecondary: '#6B7280',
  textMuted: '#9CA3AF',
  textOnPrimary: '#FFFFFF',

  border: '#E5E7EB',
  borderLight: '#F3F4F6',
  divider: '#F0F0F0',

  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',

  // Expense categories
  transport: '#3B82F6',
  accommodation: '#8B5CF6',
  food: '#F59E0B',
  ticket: '#10B981',
  shopping: '#EC4899',
  other: '#6B7280',

  // Saved/bookmarked
  saved: '#F59E0B',
  savedBg: '#FEF3C7',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export const fontSize = {
  xs: 11,
  sm: 13,
  md: 15,
  lg: 17,
  xl: 20,
  xxl: 24,
  title: 28,
};

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  full: 999,
};

// Minimum touch target: 48px (iOS HIG & Material Design)
export const touchTarget = {
  min: 48,
  button: 52,
};
