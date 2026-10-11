import { useState, useEffect } from "react";
import {
  Search,
  Filter,
  Bookmark,
  History,
  Sparkles,
  ExternalLink,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  FileText,
  Wrench,
  UserCheck,
  Box,
  Megaphone,
  File,
  ShieldAlert,
} from "lucide-react";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Loader from "../components/Loader.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Toast from "../components/Toast.jsx";
import { searchService } from "../services/searchService.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useNavigate } from "react-router-dom";

export default function GlobalSearchPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeType, setActiveType] = useState("");

  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [reindexing, setReindexing] = useState(false);

  const [savedSearches, setSavedSearches] = useState([]);
  const [history, setHistory] = useState([]);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const isStaffAdmin = ["administrator", "app_manager"].includes(user?.role);

  // Load History & Saved Searches
  useEffect(() => {
    searchService
      .getSavedSearches()
      .then((res) => setSavedSearches(res.data))
      .catch(() => {});
    searchService
      .getHistory()
      .then((res) => setHistory(res.data))
      .catch(() => {});
  }, []);

  // Fetch suggestions as user types (race-condition guarded)
  useEffect(() => {
    let active = true;
    const currentQuery = query.trim();
    if (currentQuery.length >= 2) {
      searchService
        .getSuggestions({ q: currentQuery })
        .then((res) => {
          if (active) {
            setSuggestions(res.data);
            setShowSuggestions(true);
          }
        })
        .catch(() => {
          if (active) setSuggestions([]);
        });
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
    return () => {
      active = false;
    };
  }, [query]);

  const handleSearch = async (e, customQuery = null, customType = null) => {
    if (e) e.preventDefault();
    const targetQ = customQuery !== null ? customQuery : query;
    const targetT = customType !== null ? customType : activeType;

    if (!targetQ.strip && !targetQ) return;

    setLoading(true);
    setShowSuggestions(false);
    setMessage("");
    setError("");

    try {
      const res = await searchService.search({ q: targetQ, type: targetT });
      setResults(res.data);
      // Reload history
      searchService
        .getHistory()
        .then((r) => setHistory(r.data))
        .catch(() => {});
    } catch (err) {
      setError("Search request failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCurrentSearch = async () => {
    if (!query) return;
    try {
      await searchService.saveSearch({ search_name: query, query });
      setMessage(`Saved search '${query}' to quick links.`);
      searchService
        .getSavedSearches()
        .then((res) => setSavedSearches(res.data))
        .catch(() => {});
    } catch (err) {
      setError("Failed to save search.");
    }
  };

  const handleClearHistory = async () => {
    try {
      await searchService.clearHistory();
      setHistory([]);
      setMessage("Search history cleared.");
    } catch (err) {
      setError("Failed to clear history.");
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      const res = await searchService.reindex();
      setMessage(res.data.message);
    } catch (err) {
      setError("Search reindex failed.");
    } finally {
      setReindexing(false);
    }
  };

  const getEntityIcon = (type) => {
    switch (type) {
      case "Complaint":
        return <FileText className="h-4 w-4 text-amber-500" />;
      case "WorkOrder":
        return <Wrench className="h-4 w-4 text-sky-500" />;
      case "Visitor":
        return <UserCheck className="h-4 w-4 text-indigo-500" />;
      case "Asset":
        return <Box className="h-4 w-4 text-emerald-500" />;
      case "Announcement":
        return <Megaphone className="h-4 w-4 text-purple-500" />;
      case "Audit":
        return <ShieldAlert className="h-4 w-4 text-rose-500" />;
      default:
        return <File className="h-4 w-4 text-slate-500" />;
    }
  };

  const navigateToEntity = (type, entityId) => {
    switch (type) {
      case "Complaint":
        navigate(`/complaints/${entityId}`);
        break;
      case "WorkOrder":
        navigate("/work-orders");
        break;
      case "Visitor":
        navigate("/visitors");
        break;
      case "Asset":
        navigate("/assets");
        break;
      case "Announcement":
        navigate("/announcements");
        break;
      case "Document":
        navigate("/reports");
        break;
      case "Report":
        navigate("/reports");
        break;
      default:
        navigate("/complaints");
        break;
    }
  };

  return (
    <div className="grid gap-6 max-w-6xl">
      <PageHeader
        title="Global Search Engine"
        description="Unified search across all Campus Pulse entities, complaints, work orders, visitor passes, and asset registries."
        actions={
          isStaffAdmin && (
            <Button
              onClick={handleReindex}
              disabled={reindexing}
              size="sm"
              variant="secondary"
              className="font-bold flex items-center gap-1.5"
            >
              <RefreshCw
                className={`h-4 w-4 ${reindexing ? "animate-spin" : ""}`}
              />
              {reindexing ? "Reindexing..." : "Rebuild Search Index"}
            </Button>
          )
        }
      />

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Hero Unified Search Input Bar */}
      <div className="relative">
        <form
          onSubmit={(e) => handleSearch(e)}
          className="relative flex items-center"
        >
          <Search className="absolute left-4 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search anything (e.g. Room 214, Electrician, WO-2026-0001, AST-1001)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => query.length >= 2 && setShowSuggestions(true)}
            className="w-full pl-12 pr-28 py-3.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-2xl text-sm font-semibold text-slate-900 dark:text-slate-100 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          />
          <div className="absolute right-2 flex items-center gap-1">
            <Button type="submit" size="sm" className="font-bold px-4">
              Search
            </Button>
          </div>
        </form>

        {/* Auto-Complete Suggestions Dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute left-0 right-0 top-full mt-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl z-30 overflow-hidden text-xs">
            <div className="px-3 py-2 bg-slate-50 dark:bg-slate-800/60 font-bold text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-100 dark:border-slate-800">
              Instant Auto-Complete Suggestions
            </div>
            {suggestions.map((item, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setQuery(item.title);
                  handleSearch(null, item.title);
                }}
                className="px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer flex items-center justify-between border-b border-slate-100 dark:border-slate-800 last:border-0"
              >
                <div className="flex items-center gap-2">
                  {getEntityIcon(item.entity_type)}
                  <span className="font-bold text-slate-900 dark:text-slate-100">{item.title}</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  {item.entity_type}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Module Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
        {[
          { label: "All Modules", value: "" },
          { label: "Complaints", value: "Complaint" },
          { label: "Work Orders", value: "WorkOrder" },
          { label: "Visitors", value: "Visitor" },
          { label: "Assets", value: "Asset" },
          { label: "Announcements", value: "Announcement" },
          { label: "Documents", value: "Document" },
          { label: "Audit Logs", value: "Audit" },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => {
              setActiveType(tab.value);
              if (query) handleSearch(null, query, tab.value);
            }}
            className={`px-3 py-1.5 rounded-full transition-all ${
              activeType === tab.value
                ? "bg-primary text-white font-bold shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}

        {query && (
          <button
            onClick={handleSaveCurrentSearch}
            className="ml-auto text-xs font-bold text-primary flex items-center gap-1 hover:underline"
          >
            <Bookmark className="h-3.5 w-3.5" /> Save Search
          </button>
        )}
      </div>

      <div className="grid lg:grid-cols-4 gap-6">
        {/* Results Feed Column */}
        <div className="lg:col-span-3 grid gap-3">
          {loading ? (
            <Loader
              label="Searching across Campus Pulse..."
              variant="skeleton"
            />
          ) : results.length === 0 ? (
            <EmptyState
              title={
                query ? "No matching records found" : "Enter a search query"
              }
              description={
                query
                  ? "Try searching for another keyword or room number."
                  : "Search across complaints, work orders, visitor gate passes, and campus assets."
              }
            />
          ) : (
            results.map((res) => (
              <Card
                key={res.index_id}
                onClick={() => navigateToEntity(res.entity_type, res.entity_id)}
                className="flex items-center justify-between gap-4 cursor-pointer hover:border-primary/40 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-xl shrink-0 mt-0.5">
                    {getEntityIcon(res.entity_type)}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                        {res.title}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200">
                        {res.entity_type}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 dark:text-slate-300 font-medium mt-1">
                      {res.description || "No description available."}
                    </p>
                    <div className="text-[11px] text-slate-400 font-mono font-semibold mt-1">
                      ID: {res.entity_id}
                    </div>
                  </div>
                </div>

                <Button
                  variant="subtle"
                  size="sm"
                  className="shrink-0 font-bold text-xs flex items-center gap-1"
                >
                  Open <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Card>
            ))
          )}
        </div>

        {/* Sidebar Column: Saved Searches & Recent Searches */}
        <div className="grid gap-4 self-start text-xs">
          {/* Saved Searches */}
          <Card className="grid gap-3 bg-slate-50/50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800">
            <div className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5 border-b border-slate-200 dark:border-slate-800 pb-2">
              <Bookmark className="h-4 w-4 text-primary" /> Saved Quick Searches
            </div>
            {savedSearches.length === 0 ? (
              <div className="text-slate-400 italic">
                No saved searches yet.
              </div>
            ) : (
              <div className="grid gap-2">
                {savedSearches.map((s) => (
                  <div
                    key={s.saved_search_id}
                    onClick={() => {
                      setQuery(s.query);
                      handleSearch(null, s.query);
                    }}
                    className="p-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg cursor-pointer hover:border-primary font-bold text-slate-800 dark:text-slate-100 flex items-center justify-between"
                  >
                    <span>{s.search_name}</span>
                    <Search className="h-3 w-3 text-slate-400" />
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Search History */}
          <Card className="grid gap-3 bg-slate-50/50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800">
            <div className="font-bold text-slate-900 dark:text-slate-100 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
              <span className="flex items-center gap-1.5">
                <History className="h-4 w-4 text-slate-600" /> Recent Search
                Queries
              </span>
              {history.length > 0 && (
                <button
                  onClick={handleClearHistory}
                  className="text-[10px] font-bold text-rose-600 hover:underline"
                >
                  Clear
                </button>
              )}
            </div>
            {history.length === 0 ? (
              <div className="text-slate-400 italic">No recent history.</div>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {history.slice(0, 10).map((h) => (
                  <button
                    key={h.history_id}
                    onClick={() => {
                      setQuery(h.search_query);
                      handleSearch(null, h.search_query);
                    }}
                    className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg font-semibold text-slate-700 hover:bg-slate-100 text-[11px]"
                  >
                    {h.search_query}
                  </button>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
