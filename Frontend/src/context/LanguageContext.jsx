import { createContext, useContext, useState, useEffect } from "react";
import en from "../locales/en.json";
import te from "../locales/te.json";
import hi from "../locales/hi.json";
import apiClient from "../api/axios";

const translations = { en, te, hi };

const LanguageContext = createContext(null);

export const LanguageProvider = ({ children }) => {
  const [language, setLanguageState] = useState(() => {
    return localStorage.getItem("campus_pulse_lang") || "en";
  });
  const [showPicker, setShowPicker] = useState(false);
  const [hasSeenSpeechTip, setHasSeenSpeechTip] = useState(() => {
    return localStorage.getItem("campus_pulse_speech_tip_seen") === "true";
  });

  useEffect(() => {
    // If first time visiting, prompt user to select language
    const chosen = localStorage.getItem("campus_pulse_lang_chosen");
    if (!chosen) {
      setShowPicker(true);
    }
  }, []);

  const setLanguage = async (newLang) => {
    if (!translations[newLang]) return;
    setLanguageState(newLang);
    localStorage.setItem("campus_pulse_lang", newLang);
    localStorage.setItem("campus_pulse_lang_chosen", "true");
    setShowPicker(false);

    try {
      const token = localStorage.getItem("token") || localStorage.getItem("access_token");
      if (token) {
        await apiClient.put("/users/me/language", { language: newLang });
      }
    } catch {
      // Best-effort server sync
    }
  };

  const dismissSpeechTip = () => {
    setHasSeenSpeechTip(true);
    localStorage.setItem("campus_pulse_speech_tip_seen", "true");
  };

  const t = (path, paramsOrFallback = {}) => {
    const keys = path.split(".");
    let current = translations[language] || translations.en;
    for (const key of keys) {
      if (current && typeof current === "object" && key in current) {
        current = current[key];
      } else {
        // Fallback to English
        let fallback = translations.en;
        for (const fbKey of keys) {
          if (fallback && typeof fallback === "object" && fbKey in fallback) {
            fallback = fallback[fbKey];
          } else {
            return typeof paramsOrFallback === "string" ? paramsOrFallback : path;
          }
        }
        current = fallback;
        break;
      }
    }

    if (typeof current === "string" && typeof paramsOrFallback === "object") {
      let str = current;
      for (const [paramKey, paramVal] of Object.entries(paramsOrFallback)) {
        str = str.replace(new RegExp(`\\{${paramKey}\\}`, "g"), paramVal);
      }
      return str;
    }

    return typeof current === "string" ? current : path;
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t,
        showPicker,
        setShowPicker,
        hasSeenSpeechTip,
        dismissSpeechTip,
      }}
    >
      {children}

      {/* First-Login / Language Picker Modal */}
      {showPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center animate-in fade-in zoom-in-95 duration-200">
            <div className="text-4xl mb-3">🌐</div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
              Choose your preferred language
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
              మీ భాషను ఎంచుకోండి · अपनी भाषा चुनें
            </p>

            <div className="space-y-3">
              <button
                type="button"
                onClick={() => setLanguage("en")}
                className={`w-full flex items-center justify-between px-5 py-3 rounded-xl border text-base font-semibold transition-all ${
                  language === "en"
                    ? "border-blue-600 bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200"
                }`}
              >
                <span>English</span>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-normal">EN</span>
              </button>

              <button
                type="button"
                onClick={() => setLanguage("te")}
                className={`w-full flex items-center justify-between px-5 py-3 rounded-xl border text-base font-semibold transition-all ${
                  language === "te"
                    ? "border-blue-600 bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200"
                }`}
              >
                <span>తెలుగు</span>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-normal">Telugu</span>
              </button>

              <button
                type="button"
                onClick={() => setLanguage("hi")}
                className={`w-full flex items-center justify-between px-5 py-3 rounded-xl border text-base font-semibold transition-all ${
                  language === "hi"
                    ? "border-blue-600 bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200"
                }`}
              >
                <span>हिन्दी</span>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-normal">Hindi</span>
              </button>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500">
              {t("speech_tip")}
            </div>
          </div>
        </div>
      )}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
};
