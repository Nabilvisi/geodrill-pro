export const tokens = {
  color: {
    brand: {
      deepBlue: '#0B3D91',
      teal: '#0EA5B7',
      orange: '#F97316',
      graphite: '#374151',
      stone: '#94A3B8',
    },
    semantic: {
      success: '#10B981',
      warning: '#F59E0B',
      danger: '#EF4444',
      info: '#3B82F6',
      stale: '#A855F7',
      withheld: '#64748B',
      unqualified: '#F59E0B',
      research: '#0EA5B7',
    },
    neutral: {
      background: '#F8FAFC',
      surface: '#FFFFFF',
      surfaceRaised: '#F1F5F9',
      border: '#E2E8F0',
      text: '#0F172A',
      textSecondary: '#475569',
      muted: '#94A3B8',
      darkBackground: '#0F172A',
      darkSurface: '#1E293B',
      darkBorder: '#334155',
      darkText: '#F8FAFC',
    }
  },
  spacing: {
    1: 4,
    2: 8,
    3: 12,
    4: 16,
    6: 24,
    8: 32,
    12: 48,
  },
  radius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
  },
  typography: {
    fontFamily: "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    monoFontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
  }
} as const;

export type DesignTokens = typeof tokens;
