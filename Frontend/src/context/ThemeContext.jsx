import { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [themeMode, setThemeModeState] = useState(() => {
    const saved = localStorage.getItem("campus_pulse_theme_mode");
    if (saved === "dark" || saved === "light" || saved === "system") {
      return saved;
    }
    return "system"; // Default to system theme
  });

  const [activeTheme, setActiveTheme] = useState(() => {
    if (themeMode === "dark" || themeMode === "light") {
      return themeMode;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    const root = document.documentElement;

    const resolveTheme = (mode) => {
      if (mode === "dark" || mode === "light") {
        return mode;
      }
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    };

    const current = resolveTheme(themeMode);
    setActiveTheme(current);

    if (current === "dark") {
      root.classList.add("dark");
      root.setAttribute("data-theme", "dark");
    } else {
      root.classList.remove("dark");
      root.setAttribute("data-theme", "light");
    }

    localStorage.setItem("campus_pulse_theme_mode", themeMode);

    // System theme listener
    if (themeMode === "system") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      const handleChange = (e) => {
        const newTheme = e.matches ? "dark" : "light";
        setActiveTheme(newTheme);
        if (newTheme === "dark") {
          root.classList.add("dark");
          root.setAttribute("data-theme", "dark");
        } else {
          root.classList.remove("dark");
          root.setAttribute("data-theme", "light");
        }
      };
      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }
  }, [themeMode]);

  const setThemeMode = (mode) => {
    if (mode === "dark" || mode === "light" || mode === "system") {
      setThemeModeState(mode);
    }
  };

  const toggleTheme = () => {
    setThemeModeState((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <ThemeContext.Provider
      value={{
        themeMode, // 'light' | 'dark' | 'system'
        activeTheme, // 'light' | 'dark'
        setThemeMode,
        toggleTheme,
        isDark: activeTheme === "dark",
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
