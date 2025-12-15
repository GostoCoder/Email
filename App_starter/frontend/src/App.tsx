import { useEffect, useState } from "react";
import { getApps } from "./lib/api";
import { supabase } from "./lib/supabase";
import { AppCard } from "./components/AppCard";
import { App as AppType } from "./types";

function App() {
  const [apps, setApps] = useState<AppType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log("App mounted");
    console.log("API URL:", import.meta.env.VITE_API_URL);
    console.log("Supabase URL:", import.meta.env.VITE_SUPABASE_URL);
    
    getApps()
      .then((data) => {
        console.log("Apps loaded:", data);
        setApps(data);
      })
      .catch(async (err) => {
        console.error("Error loading apps:", err);
        // fallback: try Supabase directly if backend unreachable
        try {
          const { data, error: supaError } = await supabase
            .from("apps")
            .select("id,name,url,description,icon,category,is_active,created_at,updated_at")
            .eq("is_active", true);
          if (supaError) throw supaError;
          if (data) {
            console.log("Apps loaded from Supabase:", data);
            setApps(
              data.map((app) => ({
                ...app,
                icon: app.icon || "🧩",
              }))
            );
            return;
          }
        } catch (supaErr: any) {
          console.error("Supabase error:", supaErr);
          setError(err?.message || supaErr?.message || "Erreur de chargement");
        }
      })
      .finally(() => {
        console.log("Loading complete");
        setLoading(false);
      });
  }, []);

  console.log("Rendering App - loading:", loading, "error:", error, "apps:", apps.length);

  return (
    <div className="page">
      <header className="header">
        <div>
          <p className="eyebrow">Hub-Almadia Template</p>
          <h1>App Starter</h1>
          <p className="subtitle">
            Frontend React + Backend FastAPI + Traefik-ready routing.
          </p>
        </div>
        <a className="cta" href="/health" target="_blank" rel="noreferrer">
          Healthcheck
        </a>
      </header>

      {loading && <p className="muted">Chargement...</p>}
      {error && <p className="error">{error}</p>}

      <section className="grid">
        {apps.map((app) => (
          <AppCard key={app.id} app={app} />
        ))}
      </section>
    </div>
  );
}

export default App;
