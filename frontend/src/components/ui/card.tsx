import * as React from 'react';

import { cn } from '../../lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
  border?: 'soft' | 'glow' | 'none';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hoverable = true, border = 'soft', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'relative overflow-hidden rounded-2xl border border-transparent bg-white/5 p-6 text-foreground/90 shadow-soft-inner backdrop-blur-lg transition duration-300',
        hoverable && 'hover-lift hover:border-white/10',
        border === 'glow' && 'border-white/8 shadow-glow-md',
        border === 'none' && 'border-transparent shadow-none',
        className,
      )}
      {...props}
    />
  ),
);

Card.displayName = 'Card';

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mb-5 space-y-2', className)} {...props} />;
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn('text-lg font-semibold text-foreground', className)} {...props} />;
}

export function CardDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm text-foreground/70', className)} {...props} />;
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('space-y-4', className)} {...props} />;
}

export function CardFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mt-5 flex items-center justify-between', className)} {...props} />;
}
