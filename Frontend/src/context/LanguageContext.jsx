import { createContext, useContext, useState, useEffect, useCallback } from "react";
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

  // Sync user language from backend when authenticated
  const syncUserLanguage = useCallback((userLanguage, isFirstLogin = false) => {
    if (userLanguage && translations[userLanguage]) {
      setLanguageState(userLanguage);
      localStorage.setItem("campus_pulse_lang", userLanguage);
      localStorage.setItem("campus_pulse_lang_chosen", "true");
      setShowPicker(false);
    } else if (isFirstLogin) {
      const chosen = localStorage.getItem("campus_pulse_lang_chosen");
      if (!chosen) {
        setShowPicker(true);
      }
    }
  }, []);

  useEffect(() => {
    // Check if user language is already chosen in local storage
    const chosen = localStorage.getItem("campus_pulse_lang_chosen");
    const storedLang = localStorage.getItem("campus_pulse_lang");
    if (storedLang && translations[storedLang]) {
      setLanguageState(storedLang);
    }

    // Listen for auth events dispatched from AuthContext
    const handleAuthLoaded = (e) => {
      const user = e.detail;
      if (user) {
        if (user.language && translations[user.language]) {
          setLanguageState(user.language);
          localStorage.setItem("campus_pulse_lang", user.language);
          localStorage.setItem("campus_pulse_lang_chosen", "true");
          setShowPicker(false);
        } else if (user.first_login && !chosen) {
          setShowPicker(true);
        }
      }
    };

    window.addEventListener("campus-pulse-user-loaded", handleAuthLoaded);
    return () => {
      window.removeEventListener("campus-pulse-user-loaded", handleAuthLoaded);
    };
  }, []);

  const setLanguage = async (newLang) => {
    if (!translations[newLang]) return;
    setLanguageState(newLang);
    localStorage.setItem("campus_pulse_lang", newLang);
    localStorage.setItem("campus_pulse_lang_chosen", "true");
    setShowPicker(false);

    try {
      const token = localStorage.getItem("campusPulseToken");
      if (token) {
        await apiClient.put("/users/me/language", { language: newLang });
      }
    } catch (err) {
      // Best-effort server sync; client state is already updated
      console.warn("Could not sync language with backend:", err?.message);
    }
  };

  const dismissSpeechTip = () => {
    setHasSeenSpeechTip(true);
    localStorage.setItem("campus_pulse_speech_tip_seen", "true");
  };

  const t = (path, paramsOrFallback = {}) => {
    if (!path) return "";
    const keys = path.split(".");
    let current = translations[language] || translations.en;
    let found = true;

    for (const key of keys) {
      if (current && typeof current === "object" && key in current) {
        current = current[key];
      } else {
        found = false;
        break;
      }
    }

    if (!found) {
      // Fallback to English dictionary
      let fallback = translations.en;
      for (const fbKey of keys) {
        if (fallback && typeof fallback === "object" && fbKey in fallback) {
          fallback = fallback[fbKey];
        } else {
          return typeof paramsOrFallback === "string" ? paramsOrFallback : keys[keys.length - 1];
        }
      }
      current = fallback;
    }

    if (typeof current === "string") {
      if (typeof paramsOrFallback === "object") {
        let str = current;
        for (const [paramKey, paramVal] of Object.entries(paramsOrFallback)) {
          str = str.replace(new RegExp(`\\{${paramKey}\\}`, "g"), paramVal);
        }
        return str;
      }
      return current;
    }

    return typeof paramsOrFallback === "string" ? paramsOrFallback : keys[keys.length - 1];
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        syncUserLanguage,
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
              {t("choose_language", "Choose your preferred language")}
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
              మీ భాషను ఎంచుకోండి · अपनी भाषा चुनें
            </p>

            <div className="space-y-3">
              <button
                type="button"
                onClick={() => setLanguage("en")}
                className={`w-full flex items-center justify-between px-5 py-3 rounded-xl border text-base font-semibold transition-all cursor-pointer ${
                  language === "en"
                    ? "border-primary bg-primary/10 text-primary shadow-xs"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200"
                }`}
              >
                <span>English</span>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-normal">EN</span>
              </button>

              <button
                type="button"
                onClick={() => setLanguage("te")}
                className={`w-full flex items-center justify-between px-5 py-3 rounded-xl border text-base font-semibold transition-all cursor-pointer ${
                  language === "te"
                    ? "border-primary bg-primary/10 text-primary shadow-xs"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200"
                }`}
              >
                <span>తెలుగు</span>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-normal">Telugu</span>
              </button>

              <button
                type="button"
                onClick={() => setLanguage("hi")}
                className={`w-full flex items-center justify-between px-5 py-3 rounded-xl border text-base font-semibold transition-all cursor-pointer ${
                  language === "hi"
                    ? "border-primary bg-primary/10 text-primary shadow-xs"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200"
                }`}
              >
                <span>हिन्दी</span>
                <span className="text-xs uppercase tracking-wider text-slate-500 font-normal">Hindi</span>
              </button>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
              <span>{t("speech_tip")}</span>
              <button
                type="button"
                onClick={() => setShowPicker(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 underline cursor-pointer"
              >
                {t("common.close", "Close")}
              </button>
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
