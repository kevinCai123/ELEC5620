import * as React from 'react';

import { cn } from '../../lib/utils';

type PageSectionProps = React.HTMLAttributes<HTMLDivElement>;

export function PageSection({ className, ...props }: PageSectionProps) {
  return <div className={cn('mx-auto w-full max-w-[1400px] px-4 sm:px-6 lg:px-8 xl:px-10', className)} {...props} />;
}
