import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Bell,
  BookOpenCheck,
  Brain,
  CalendarClock,
  Compass,
  FileText,
  Home,
  Mail,
  Menu,
  MessageSquareQuote,
  Settings,
  Sparkles,
  Waypoints,
} from 'lucide-react';

import AppShellLayout from '../layout/AppShell';
import { PageSection } from '../layout/PageSection';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '../ui/command';
import { Dialog, DialogContent } from '../ui/dialog';
import { Drawer, DrawerContent, DrawerTrigger } from '../ui/drawer';
import { Kbd } from '../ui/kbd';
import { Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip';
import { ThemeToggle } from './ThemeToggle';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: Home },
  { label: 'Emails', path: '/emails', icon: Mail },
  { label: 'Study Plan', path: '/study/plan', icon: CalendarClock },
  { label: 'Summarize', path: '/summarize', icon: FileText },
  { label: 'Quiz', path: '/quiz', icon: Brain },
  { label: 'Travel', path: '/travel', icon: Waypoints },
  { label: 'To-Do', path: '/todo', icon: MessageSquareQuote },
  { label: 'Places', path: '/places', icon: Compass },
  { label: 'Digest', path: '/digest/preview', icon: BookOpenCheck },
  { label: 'Settings', path: '/settings', icon: Settings },
];

const QUICK_LINKS = NAV_ITEMS.filter((item) => item.path !== '/digest/preview');

const PATH_LABELS: Record<string, string> = {
  '/': 'Dashboard',
  '/emails': 'Emails',
  '/study': 'Study',
  '/study/plan': 'Study Plan',
  '/summarize': 'Summarize',
  '/quiz': 'Quiz',
  '/travel': 'Travel',
  '/todo': 'To-Do',
  '/places': 'Places',
  '/digest': 'Digest',
  '/digest/preview': 'Digest Preview',
  '/settings': 'Settings',
};

function buildBreadcrumbs(pathname: string) {
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) {
    return [{ label: 'Dashboard', path: '/' }];
  }

  const crumbs = [{ label: 'Dashboard', path: '/' }];
  let cumulativePath = '';
  segments.forEach((segment) => {
    cumulativePath += `/${segment}`;
    const match = NAV_ITEMS.find((item) => item.path === cumulativePath);
    const label =
      match?.label ??
      PATH_LABELS[cumulativePath] ??
      segment.replace(/-/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
    if (!crumbs.length || crumbs[crumbs.length - 1].path !== cumulativePath) {
      crumbs.push({
        label,
        path: cumulativePath,
      });
    }
  });
  return crumbs;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setIsCommandOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  useEffect(() => {
    setIsDrawerOpen(false);
  }, [location.pathname]);

  const breadcrumbs = useMemo(() => buildBreadcrumbs(location.pathname), [location.pathname]);

  const renderNavLink = (item: (typeof NAV_ITEMS)[number]) => {
    const Icon = item.icon;
    const isActive =
      location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));

    return (
      <Link
        key={item.path}
        to={item.path}
        className={`group relative flex min-w-0 items-center gap-2.5 overflow-hidden rounded-xl px-3 py-2 text-sm font-medium transition duration-200 ease-aurora ${
          isActive
            ? 'bg-white/10 text-foreground shadow-glow-md drop-shadow-glow'
            : 'text-foreground/60 hover:bg-white/5 hover:text-foreground'
        }`}
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-foreground">
          <Icon className="h-3.5 w-3.5" />
        </span>
        <span className="truncate text-[13px]">{item.label}</span>
        {isActive && <span className="absolute inset-0 -z-10 bg-aurora opacity-20" />}
      </Link>
    );
  };

  const sidebarContent = (
    <div className="flex h-full w-full flex-col gap-3 px-4 py-5 lg:px-5">
      <Link to="/" className="flex items-center gap-3 pb-4 text-foreground">
        <motion.span
          className="flex h-10 w-10 items-center justify-center rounded-2xl bg-aurora text-lg font-bold text-background shadow-glow-md"
          layoutId="logo"
        >
          AI
        </motion.span>
        <div className="min-w-0">
          <p className="text-sm font-semibold leading-tight">Study Companion</p>
          <p className="text-[10px] uppercase tracking-[0.24em] text-foreground/50">ELEC5620</p>
        </div>
      </Link>
      <nav className="flex flex-1 flex-col gap-0.5">{NAV_ITEMS.map(renderNavLink)}</nav>
    </div>
  );

  const headerContent = (
    <div className="flex h-[var(--header-h)] items-center justify-between gap-4 px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <Drawer open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
          <DrawerTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden" glow={false} aria-label="Toggle menu">
              <Menu className="h-5 w-5" />
            </Button>
          </DrawerTrigger>
          <DrawerContent className="h-full w-[min(90vw,320px)] overflow-y-auto overscroll-contain border-r border-white/10 bg-background/95 px-4 py-8">
            <nav className="flex flex-col gap-0.5">{NAV_ITEMS.map(renderNavLink)}</nav>
          </DrawerContent>
        </Drawer>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.28em] text-foreground/40">
            {breadcrumbs.map((crumb, index) => (
              <span key={crumb.path} className="flex items-center gap-2">
                {index > 0 && <span className="text-foreground/30">/</span>}
                <Link
                  to={crumb.path}
                  className={
                    index === breadcrumbs.length - 1
                      ? 'truncate text-foreground/80'
                      : 'truncate text-foreground/60 hover:text-foreground'
                  }
                >
                  {crumb.label}
                </Link>
              </span>
            ))}
          </div>
          <h1 className="mt-1 truncate text-xl font-semibold text-foreground">
            {breadcrumbs.at(-1)?.label ?? 'Dashboard'}
          </h1>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <Dialog open={isCommandOpen} onOpenChange={setIsCommandOpen}>
          <Button
            type="button"
            variant="secondary"
            className="hidden h-10 min-w-[220px] justify-between rounded-lg px-4 lg:flex"
            onClick={() => setIsCommandOpen(true)}
          >
            <span className="flex items-center gap-2 text-sm text-foreground/70">
              <Sparkles className="h-4 w-4" />
              Search workspace
            </span>
            <span className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-foreground/40">
              <Kbd>⌘K</Kbd>
            </span>
          </Button>
          <DialogContent className="max-h-[80dvh] max-w-2xl overflow-hidden border-white/10 bg-background/95 p-0">
            <Command label="Global command menu">
              <CommandInput placeholder="Where to next?" />
              <CommandList className="max-h-[60dvh] overflow-y-auto">
                <CommandEmpty>No routes match that query.</CommandEmpty>
                <CommandGroup heading="Navigate">
                  {NAV_ITEMS.map((item) => (
                    <CommandItem
                      key={item.path}
                      value={item.label}
                      onSelect={() => {
                        navigate(item.path);
                        setIsCommandOpen(false);
                      }}
                    >
                      <item.icon className="h-4 w-4 opacity-60" />
                      {item.label}
                    </CommandItem>
                  ))}
                </CommandGroup>
                <CommandGroup heading="Quick actions">
                  {QUICK_LINKS.map((item) => (
                    <CommandItem
                      key={`quick-${item.path}`}
                      value={`Quick ${item.label}`}
                      onSelect={() => {
                        navigate(item.path);
                        setIsCommandOpen(false);
                      }}
                    >
                      <Sparkles className="h-4 w-4 opacity-60" />
                      Create {item.label}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          </DialogContent>
        </Dialog>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="ghost" size="icon" glow={false} aria-label="Notifications" className="h-10 w-10 rounded-lg">
              <Bell className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent className="z-30">Notifications coming soon</TooltipContent>
        </Tooltip>
        <ThemeToggle />
        <Button
          variant="ghost"
          glow={false}
          className="hidden h-10 items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 text-sm font-medium text-foreground/80 xl:flex"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-aurora text-background shadow-glow-md">
            SC
          </span>
          Profile
        </Button>
      </div>
    </div>
  );

  return (
    <AppShellLayout sidebar={sidebarContent} header={headerContent}>
      <div className="relative flex min-h-full w-full flex-col overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 top-0 z-1 mx-auto h-[320px] max-w-5xl bg-aurora opacity-30 blur-3xl" />
        <PageSection className="flex min-h-0 flex-1 flex-col pb-16 pt-8">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
            className="min-w-0 w-full space-y-8"
          >
            {children}
          </motion.div>
        </PageSection>
      </div>
    </AppShellLayout>
  );
}
