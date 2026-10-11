import { Download } from "lucide-react";
import SearchBar from "./SearchBar.jsx";
import Select from "./Select.jsx";
import Button from "./Button.jsx";

export default function TableToolbar({
  searchValue,
  onSearchChange,
  searchPlaceholder = "Search records...",
  filters = [], // Array of { label, value, onChange, options: [{ value, label }] }
  onExport,
  actions,
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm mb-4 text-slate-900 dark:text-slate-100">
      {/* Search and Filters group */}
      <div className="flex flex-wrap items-center gap-3 flex-1 min-w-0">
        {onSearchChange !== undefined && (
          <SearchBar
            value={searchValue}
            onChange={onSearchChange}
            placeholder={searchPlaceholder}
          />
        )}

        {filters.map((filter, index) => (
          <div key={index} className="min-w-44">
            <Select
              id={`table-filter-${index}`}
              aria-label={filter.label}
              value={filter.value}
              onChange={(e) => filter.onChange(e.target.value)}
            >
              <option value="">All {filter.label}</option>
              {filter.options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </div>
        ))}
      </div>

      {/* Export & Actions group */}
      <div className="flex items-center gap-2">
        {onExport && (
          <Button
            variant="subtle"
            size="sm"
            onClick={onExport}
            className="h-12 px-4 rounded-xl text-xs font-bold"
          >
            <Download className="h-4 w-4 mr-1.5 shrink-0" />
            Export CSV
          </Button>
        )}
        {actions}
      </div>
    </div>
  );
}
