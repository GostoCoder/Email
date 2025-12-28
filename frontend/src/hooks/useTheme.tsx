import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  isDark: boolean;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Get system preference
const getSystemTheme = (): boolean => {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
};

// Get stored theme
const getStoredTheme = (): Theme => {
  const stored = localStorage.getItem('app_theme');
  if (stored && ['light', 'dark', 'system'].includes(stored)) {
    return stored as Theme;
  }
  return 'system';
};

// Apply theme to document
const applyTheme = (isDark: boolean) => {
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  document.documentElement.classList.toggle('dark', isDark);
  
  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', isDark ? '#1a1a2e' : '#ffffff');
  }
};

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getStoredTheme());
  const [isDark, setIsDark] = useState<boolean>(() => {
    const storedTheme = getStoredTheme();
    if (storedTheme === 'system') {
      return getSystemTheme();
    }
    return storedTheme === 'dark';
  });

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      if (theme === 'system') {
        setIsDark(e.matches);
        applyTheme(e.matches);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  // Apply theme on changes
  useEffect(() => {
    applyTheme(isDark);
  }, [isDark]);

  const setTheme = useCallback((newTheme: Theme) => {
    localStorage.setItem('app_theme', newTheme);
    setThemeState(newTheme);
    
    if (newTheme === 'system') {
      const systemDark = getSystemTheme();
      setIsDark(systemDark);
    } else {
      setIsDark(newTheme === 'dark');
    }
  }, []);

  const toggleTheme = useCallback(() => {
    if (theme === 'system') {
      setTheme(isDark ? 'light' : 'dark');
    } else {
      setTheme(isDark ? 'light' : 'dark');
    }
  }, [theme, isDark, setTheme]);

  return (
    <ThemeContext.Provider value={{ theme, isDark, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Theme toggle button component
export function ThemeToggle() {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="theme-toggle"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Mode clair' : 'Mode sombre'}
    >
      {isDark ? (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="5" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
        </svg>
      ) : (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  );
}

// Theme selector component
export function ThemeSelector() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="theme-selector">
      <label htmlFor="theme-select">Thème:</label>
      <select
        id="theme-select"
        value={theme}
        onChange={(e) => setTheme(e.target.value as Theme)}
        className="theme-select"
      >
        <option value="system">Système</option>
        <option value="light">Clair</option>
        <option value="dark">Sombre</option>
      </select>
    </div>
  );
}
