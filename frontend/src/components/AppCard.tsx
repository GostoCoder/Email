import { App } from "../types";

type Props = {
  app: App;
};

export function AppCard({ app }: Props) {
  return (
    <article className="card">
      <div className="card__header">
        <span className="icon">{app.icon}</span>
        <div>
          <h3>{app.name}</h3>
          <p className="muted">{app.category}</p>
        </div>
      </div>
      <p className="body">{app.description}</p>
      <div className="card__footer">
        <span className={app.is_active ? "badge badge--success" : "badge"}>
          {app.is_active ? "Actif" : "Inactif"}
        </span>
        <a className="link" href={app.url} target="_blank" rel="noreferrer">
          Ouvrir →
        </a>
      </div>
    </article>
  );
}
