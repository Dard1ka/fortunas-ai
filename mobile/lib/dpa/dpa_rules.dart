// mobile/lib/dpa/dpa_rules.dart
/// Pure helpers for editing DPA rule lists. No Flutter/Riverpod deps —
/// unit-tested directly so the risky list logic never needs a widget.
library;

/// Returns a NEW list with [value] appended after trimming. Ignores empty
/// input and case-insensitive duplicates (keeps the existing entry).
List<String> addRule(List<String> rules, String value) {
  final trimmed = value.trim();
  if (trimmed.isEmpty) return List<String>.from(rules);
  final exists = rules.any((r) => r.toLowerCase() == trimmed.toLowerCase());
  if (exists) return List<String>.from(rules);
  return [...rules, trimmed];
}

/// Returns a NEW list with the entry at [index] removed. Out-of-range index
/// returns an unchanged copy (safe — no throw).
List<String> removeRuleAt(List<String> rules, int index) {
  if (index < 0 || index >= rules.length) return List<String>.from(rules);
  final copy = List<String>.from(rules);
  copy.removeAt(index);
  return copy;
}
