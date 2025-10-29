import * as React from 'react';

import { cn } from '../../lib/utils';

export interface KbdProps extends React.HTMLAttributes<HTMLSpanElement> {}

export function Kbd({ className, ...props }: KbdProps) {
  return (
    <span
      className={cn(
        'inline-flex min-w-[28px] items-center justify-center rounded-md border border-white/15 bg-white/10 px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-foreground/80 shadow-soft-inner',
        className,
      )}
      {...props}
    />
  );
}
