import * as React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import { cn } from '../../lib/utils';

const Drawer = DialogPrimitive.Root;

const DrawerTrigger = DialogPrimitive.Trigger;

const DrawerPortal = ({ children, ...props }: DialogPrimitive.DialogPortalProps) => {
  const container =
    typeof document === 'undefined' ? undefined : document.getElementById('portal-root') ?? undefined;
  return (
    <DialogPrimitive.Portal container={container} {...props}>
      {children}
    </DialogPrimitive.Portal>
  );
};

const DrawerClose = DialogPrimitive.Close;

const DrawerOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn('fixed inset-0 z-40 bg-black/60 backdrop-blur-[2px]', className)}
    {...props}
  />
));
DrawerOverlay.displayName = DialogPrimitive.Overlay.displayName;

type DrawerContentProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> & {
  side?: 'left' | 'right';
};

const DrawerContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  DrawerContentProps
>(({ className, children, side = 'left', ...props }, ref) => (
  <DrawerPortal>
    <DrawerOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        'fixed z-50 h-full w-[90vw] max-w-sm overflow-y-auto overscroll-contain bg-background/95 p-6 text-foreground shadow-glow-md backdrop-blur-xl transition duration-200',
        side === 'left' && 'inset-y-0 left-0 data-[state=open]:animate-in data-[state=open]:slide-in-from-left data-[state=closed]:animate-out data-[state=closed]:slide-out-to-left',
        side === 'right' && 'inset-y-0 right-0 data-[state=open]:animate-in data-[state=open]:slide-in-from-right data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right',
        className,
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-full border border-foreground/10 bg-foreground/[0.05] p-2 text-foreground/70 transition hover:bg-foreground/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40">
        <X className="h-4 w-4" aria-hidden="true" />
        <span className="sr-only">Close drawer</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DrawerPortal>
));
DrawerContent.displayName = DialogPrimitive.Content.displayName;

export { Drawer, DrawerClose, DrawerContent, DrawerOverlay, DrawerPortal, DrawerTrigger };
