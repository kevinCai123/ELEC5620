import * as React from 'react';

import { cn } from '../../lib/utils';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, type, ...props }, ref) => (
  <input
    type={type}
    className={cn(
      'flex h-11 w-full items-center rounded-xl border border-white/10 bg-white/5 px-4 text-sm text-foreground placeholder:text-foreground/40 shadow-soft-inner transition duration-200 ease-aurora focus:border-primary/70 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-2 focus:ring-offset-transparent disabled:cursor-not-allowed disabled:opacity-50',
      className,
    )}
    ref={ref}
    {...props}
  />
));

Input.displayName = 'Input';
