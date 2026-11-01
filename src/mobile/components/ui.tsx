/**
 * Small shared building blocks for the mobile management panels.
 */

import { View, Text, TouchableOpacity, StyleSheet } from 'react-native'

export interface ChipOption<T extends string | number> {
  value: T
  label: string
}

export function Chips<T extends string | number>({
  options,
  value,
  onChange,
  testIDPrefix,
}: {
  options: ChipOption<T>[]
  value: T
  onChange: (v: T) => void
  testIDPrefix: string
}) {
  return (
    <View style={ui.chipRow}>
      {options.map((o) => {
        const selected = o.value === value
        return (
          <TouchableOpacity
            key={String(o.value)}
            testID={`${testIDPrefix}-${o.value}`}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            onPress={() => onChange(o.value)}
            style={[ui.chip, selected && ui.chipSelected]}
          >
            <Text style={[ui.chipText, selected && ui.chipTextSelected]}>{o.label}</Text>
          </TouchableOpacity>
        )
      })}
    </View>
  )
}

export const ui = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginTop: 16,
  },
  title: { fontSize: 18, fontWeight: '700', color: '#111827' },
  subtitle: { fontSize: 13, color: '#6b7280', marginTop: 4, marginBottom: 12 },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    marginTop: 8,
    color: '#111827',
  },
  multiline: { minHeight: 72, textAlignVertical: 'top' },
  button: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 12,
  },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  ghostButton: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  ghostButtonText: { color: '#374151', fontSize: 12 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 },
  chip: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
  },
  chipSelected: { backgroundColor: '#2563eb', borderColor: '#2563eb' },
  chipText: { fontSize: 13, color: '#374151' },
  chipTextSelected: { color: '#fff' },
  row: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  rowTitle: { fontSize: 14, fontWeight: '600', color: '#111827' },
  rowBody: { fontSize: 13, color: '#374151', marginTop: 4 },
  rowMeta: { fontSize: 12, color: '#6b7280', marginTop: 4 },
  ok: { color: '#15803d', fontSize: 13, marginTop: 8 },
  error: { color: '#b91c1c', fontSize: 13, marginTop: 8 },
  empty: { color: '#6b7280', fontSize: 13, marginTop: 8 },
})
