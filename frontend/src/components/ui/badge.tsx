import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '../../lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-pill border border-transparent px-3 py-[6px] text-xs font-semibold uppercase tracking-[0.2em]',
  {
    variants: {
      variant: {
        default: 'border-foreground/15 bg-foreground/10 text-foreground/70',
        glow: 'border-primary/30 bg-primary/10 text-primary',
        outline: 'border-foreground/25 bg-transparent text-foreground/80',
        success: 'border-emerald-400/50 bg-emerald-400/10 text-emerald-300',
        warning: 'border-amber-400/60 bg-amber-400/10 text-amber-300',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
