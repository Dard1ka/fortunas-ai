/// Groups [items] into rows of two for a 2-column KPI grid.
/// A leftover odd item becomes its own singleton row (the screen renders
/// a singleton row full-width). Scales to any N:
///   [] -> []   [a] -> [[a]]   [a,b] -> [[a,b]]   [a,b,c] -> [[a,b],[c]]
List<List<T>> pairRows<T>(List<T> items) {
  final rows = <List<T>>[];
  for (var i = 0; i < items.length; i += 2) {
    final end = (i + 2 <= items.length) ? i + 2 : items.length;
    rows.add(items.sublist(i, end));
  }
  return rows;
}
