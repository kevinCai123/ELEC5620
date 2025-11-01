import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group';
import * as React from 'react';

import { cn } from '../../lib/utils';

const SegmentedControl = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root>
>(({ className, ...props }, ref) => (
  <ToggleGroupPrimitive.Root
    ref={ref}
    className={cn(
      'inline-flex items-center gap-1 rounded-pill border border-foreground/10 bg-foreground/[0.05] p-1 shadow-soft-inner',
      className,
    )}
    {...props}
  />
));
SegmentedControl.displayName = ToggleGroupPrimitive.Root.displayName;

const SegmentedControlItem = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item>
>(({ className, ...props }, ref) => (
  <ToggleGroupPrimitive.Item
    ref={ref}
    className={cn(
      'inline-flex min-w-[84px] items-center justify-center rounded-pill px-4 py-2 text-sm font-medium text-foreground/70 transition duration-200 ease-aurora data-[state=on]:bg-primary data-[state=on]:text-background data-[state=on]:shadow-glow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
      className,
    )}
    {...props}
  />
));
SegmentedControlItem.displayName = ToggleGroupPrimitive.Item.displayName;

export { SegmentedControl, SegmentedControlItem };
