export function formatDate(value) {
  if (!value) return "-";
  try {
    const str = typeof value === "string" ? value.replace(" ", "T") : value;
    const date = new Date(str);
    if (isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  } catch {
    return String(value) || "-";
  }
}
