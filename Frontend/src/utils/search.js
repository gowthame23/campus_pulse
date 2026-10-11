export function matchesSearch(record, query, fields) {
  if (!query) return true;
  const value = query.toLowerCase();
  return fields.some((field) =>
    String(record[field] ?? "")
      .toLowerCase()
      .includes(value),
  );
}
