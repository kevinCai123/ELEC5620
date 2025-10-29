import { Toaster as SonnerToaster } from 'sonner';

export function Toaster() {
  return (
    <SonnerToaster
      theme="dark"
      toastOptions={{
        classNames: {
          toast:
            'group border border-white/10 bg-background/95 text-foreground shadow-glow-md backdrop-blur-2xl',
          title: 'text-sm font-semibold text-foreground',
          description: 'text-xs text-foreground/70',
          actionButton:
            'rounded-pill bg-primary px-3 py-1 text-xs font-semibold text-background transition hover:opacity-90',
          cancelButton:
            'rounded-pill border border-white/15 px-3 py-1 text-xs font-semibold text-foreground/70 transition hover:bg-white/10',
        },
      }}
    />
  );
}
