import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion, useMotionValue, useSpring } from 'framer-motion';

import { cn } from '../../lib/utils';

export const buttonVariants = cva(
  'group relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-pill px-5 py-2.5 text-sm font-semibold transition duration-200 ease-aurora focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-transparent disabled:cursor-not-allowed disabled:opacity-60',
  {
    variants: {
      variant: {
        primary:
          'bg-primary text-background shadow-glow-md hover:shadow-glow-lg focus-visible:ring-primary/60 active:scale-[0.98]',
        secondary:
          'border border-white/12 bg-white/10 text-foreground backdrop-blur-md hover:bg-white/15 active:scale-[0.985]',
        ghost:
          'bg-transparent text-foreground/80 hover:text-foreground hover:bg-white/8 active:scale-[0.985]',
        outline:
          'border border-white/15 bg-transparent text-foreground/80 hover:border-white/25 hover:bg-white/8 active:scale-[0.985]',
        destructive:
          'bg-red-500/90 text-white hover:bg-red-500 focus-visible:ring-red-500/60 active:scale-[0.98]',
        subtle:
          'bg-foreground/10 text-foreground/80 hover:bg-foreground/20 focus-visible:ring-foreground/50 active:scale-[0.985]',
      },
      size: {
        sm: 'px-3.5 py-2 text-xs',
        md: 'px-5 py-2.5 text-sm',
        lg: 'px-6 py-3 text-base',
        icon: 'h-10 w-10 justify-center p-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  glow?: boolean;
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      glow = true,
      asChild = false,
      children,
      onMouseMove,
      onMouseLeave,
      ...props
    },
    ref,
  ) => {
    const x = useMotionValue(0);
    const y = useMotionValue(0);
    const mouseXSpring = useSpring(x, { stiffness: 300, damping: 30 });
    const mouseYSpring = useSpring(y, { stiffness: 300, damping: 30 });

    const handleMouseMove = (event: React.MouseEvent<HTMLElement>) => {
      const target = event.currentTarget as HTMLElement;
      const rect = target.getBoundingClientRect();
      const relativeX = event.clientX - rect.left;
      const relativeY = event.clientY - rect.top;
      x.set(relativeX - rect.width / 2);
      y.set(relativeY - rect.height / 2);
      onMouseMove?.(event as React.MouseEvent<HTMLButtonElement>);
    };

    const handleMouseLeave = (event: React.MouseEvent<HTMLElement>) => {
      x.set(0);
      y.set(0);
      onMouseLeave?.(event as React.MouseEvent<HTMLButtonElement>);
    };

    const Component = asChild ? Slot : 'button';

    return (
      <Component
        className={cn(buttonVariants({ variant, size }), className)}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        ref={asChild ? undefined : ref}
        {...props}
      >
        <span className="relative inline-flex items-center gap-2">
          {glow && (
            <motion.span
              aria-hidden="true"
              className="pointer-events-none absolute left-1/2 top-1/2 h-[260%] w-[260%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(110,122,255,0.22),transparent_65%)] opacity-0 transition-opacity duration-200 group-hover:opacity-100"
              style={{ x: mouseXSpring, y: mouseYSpring }}
            />
          )}
          <span className="relative flex items-center gap-2">{children}</span>
        </span>
      </Component>
    );
  },
);

Button.displayName = 'Button';
