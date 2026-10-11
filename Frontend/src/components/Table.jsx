import { useMemo, useState } from "react";
import Button from "./Button.jsx";

export default function Table({ columns = [], rows, data, getRowKey, pageSize = 8 }) {
  const rawRows = Array.isArray(rows) ? rows : Array.isArray(data) ? data : [];
  const defaultSortKey = columns[0]?.key || columns[0]?.accessor || "";
  const [sortKey, setSortKey] = useState(defaultSortKey);
  const [direction, setDirection] = useState("asc");
  const [page, setPage] = useState(1);

  const sortedRows = useMemo(() => {
    const copy = [...rawRows];
    if (!sortKey) return copy;
    copy.sort((a, b) => {
      const col = columns.find((c) => c.key === sortKey || c.accessor === sortKey);
      const accessor = col?.accessor || col?.key || sortKey;
      const first = String(a[sortKey] ?? a[accessor] ?? "").toLowerCase();
      const second = String(b[sortKey] ?? b[accessor] ?? "").toLowerCase();
      const result = first.localeCompare(second);
      return direction === "asc" ? result : -result;
    });
    return copy;
  }, [rawRows, sortKey, direction, columns]);

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const visibleRows = sortedRows.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize,
  );

  const toggleSort = (column) => {
    if (column.sortable === false) return;
    const colKey = column.key || column.accessor;
    if (sortKey === colKey) {
      setDirection((value) => (value === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(colKey);
      setDirection("asc");
    }
    setPage(1);
  };

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#101726] shadow-2xs transition-shadow duration-200">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100 dark:divide-slate-800/80 text-sm">
          <thead className="bg-slate-50/80 dark:bg-slate-800/50 text-left text-[11px] uppercase font-semibold tracking-wider text-slate-500 dark:text-slate-400">
            <tr>
              {columns.map((column, colIdx) => (
                <th
                  key={column.key || column.accessor || column.header || colIdx}
                  className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300"
                >
                  <button
                    type="button"
                    onClick={() => toggleSort(column)}
                    className="inline-flex items-center gap-1.5 rounded hover:text-primary disabled:cursor-default disabled:hover:text-slate-500 dark:disabled:hover:text-slate-400 font-semibold"
                    disabled={column.sortable === false}
                  >
                    {column.header}
                    {sortKey === column.key && (
                      <span
                        aria-label={`sorted ${direction}`}
                        className="text-primary"
                      >
                        {direction === "asc" ? (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-3.5 w-3.5"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                        ) : (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-3.5 w-3.5"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </span>
                    )}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {visibleRows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-slate-400 dark:text-slate-500 font-medium"
                >
                  No matching records found.
                </td>
              </tr>
            ) : (
              visibleRows.map((row, rowIdx) => (
                <tr
                  key={getRowKey ? getRowKey(row) : (row.user_id || row.id || row.complaint_id || rowIdx)}
                  className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors duration-150"
                >
                  {columns.map((column, colIdx) => (
                    <td
                      key={column.key || column.accessor || column.header || colIdx}
                      className="px-4 py-3.5 text-slate-700 dark:text-slate-200 font-medium"
                    >
                      {column.render
                        ? column.render(row)
                        : (row[column.key] ?? (column.accessor ? row[column.accessor] : ""))}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 dark:border-slate-800 px-4 py-3 text-xs text-slate-500 dark:text-slate-400 bg-white dark:bg-[#101726]">
        <span className="font-medium">
          Showing {visibleRows.length} of {rawRows.length} records
        </span>
        <div className="flex items-center gap-3">
          <Button
            size="sm"
            variant="subtle"
            disabled={currentPage <= 1}
            onClick={() => setPage((value) => value - 1)}
            className="!min-h-8"
          >
            Previous
          </Button>
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            size="sm"
            variant="subtle"
            disabled={currentPage >= totalPages}
            onClick={() => setPage((value) => value + 1)}
            className="!min-h-8"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
