import * as React from 'react';

import { cn } from '../../lib/utils';

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      className={cn(
        'flex min-h-[120px] w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground placeholder:text-foreground/40 shadow-soft-inner transition duration-200 ease-aurora focus:border-primary/70 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-2 focus:ring-offset-transparent disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);

Textarea.displayName = 'Textarea';
