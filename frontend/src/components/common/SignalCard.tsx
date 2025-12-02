import type { ReactNode } from 'react';

interface SignalCardProps {
  title: string;
  stage?: string;
  children?: ReactNode;
  action?: ReactNode;
  status?: string;
}

export function SignalCard({ title, stage, children, action, status }: SignalCardProps) {
  return (
    <section className="signal-card">
      <header className="signal-card__header">
        <div>
          <p className="signal-card__stage">{stage}</p>
          <h3 className="signal-card__title">{title}</h3>
        </div>
        {action}
      </header>
      {status && <p className="signal-card__status">{status}</p>}
      <div className="signal-card__body">{children}</div>
    </section>
  );
}
