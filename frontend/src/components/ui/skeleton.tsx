import * as React from 'react';

import { cn } from '../../lib/utils';

export type SkeletonProps = React.HTMLAttributes<HTMLDivElement>;

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl bg-foreground/[0.08]',
        "before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_1.8s_infinite] before:bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.25),transparent)]",
        className,
      )}
      {...props}
    />
  );
}
