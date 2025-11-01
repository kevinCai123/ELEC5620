import * as React from 'react';

type AppShellProps = {
  sidebar: React.ReactNode;
  header: React.ReactNode;
  children: React.ReactNode;
};

export default function AppShell({ sidebar, header, children }: AppShellProps) {
  return (
    <div
      className="flex h-screen-safe min-h-screen w-full flex-col overflow-hidden md:grid"
      style={{ gridTemplateRows: 'var(--header-h) 1fr', gridTemplateColumns: 'var(--sidebar-w) 1fr' }}
    >
      <header className="col-span-2 row-start-1 row-end-2 z-20 flex-shrink-0 border-b border-foreground/10 bg-background">
        {header}
      </header>
      <aside className="row-start-2 col-start-1 col-end-2 hidden w-[var(--sidebar-w)] flex-shrink-0 overflow-hidden border-r border-foreground/[0.05] bg-background md:block">
        {sidebar}
      </aside>
      <main className="row-start-2 col-start-1 col-end-3 min-h-0 min-w-0 flex-1 overflow-x-hidden overflow-y-auto overscroll-contain bg-background md:col-start-2 md:col-end-3">
        {children}
      </main>
    </div>
  );
}
