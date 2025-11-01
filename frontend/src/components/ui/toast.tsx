import { Toaster as SonnerToaster } from 'sonner';

export function Toaster() {
  return (
    <SonnerToaster
      theme="dark"
      toastOptions={{
        classNames: {
          toast:
            'group border border-foreground/10 bg-background/95 text-foreground shadow-glow-md backdrop-blur-2xl',
          title: 'text-sm font-semibold text-foreground',
          description: 'text-xs text-foreground/70',
          actionButton:
            'rounded-pill bg-primary px-3 py-1 text-xs font-semibold text-background transition hover:opacity-90',
          cancelButton:
            'rounded-pill border border-foreground/15 px-3 py-1 text-xs font-semibold text-foreground/70 transition hover:bg-foreground/10',
        },
      }}
    />
  );
}
