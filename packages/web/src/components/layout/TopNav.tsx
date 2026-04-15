import { NavLink, Link } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { LayoutDashboard, MessageSquare, Workflow, Settings, BookOpen } from 'lucide-react';
import { listWorkflowRuns, getUpdateCheck } from '@/lib/api';
import { cn } from '@/lib/utils';

const tabs = [
  { to: '/chat', end: false, icon: MessageSquare, label: 'Chat' },
  { to: '/dashboard', end: true, icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/workflows', end: false, icon: Workflow, label: 'Workflows' },
  { to: '/library', end: true, icon: BookOpen, label: 'Library' },
  { to: '/settings', end: false, icon: Settings, label: 'Settings' },
] as const;

export function TopNav(): React.ReactElement {
  const { data: runningRuns } = useQuery({
    queryKey: ['workflowRuns', { status: 'running' }],
    queryFn: () => listWorkflowRuns({ status: 'running', limit: 1 }),
    refetchInterval: 10_000,
  });
  const hasRunning = (runningRuns?.length ?? 0) > 0;

  const { data: updateCheck } = useQuery({
    queryKey: ['update-check'],
    queryFn: getUpdateCheck,
    staleTime: 60 * 60 * 1000,
    refetchInterval: 60 * 60 * 1000,
    retry: false,
  });

  return (
    <nav className="glass-panel relative z-20 flex items-center gap-1 border-x-0 border-t-0 border-b border-border px-4">
      {/* Brand mark — GB signature with terracotta halo */}
      <Link
        to="/chat"
        className="hover-mini mr-6 flex items-center py-2"
        aria-label="GB Automation"
      >
        <div className="relative flex h-9 w-9 items-center justify-center">
          <div className="absolute inset-0 rounded-full bg-[#D97757]/25 blur-lg" />
          <img
            src="/gb-logo.png"
            alt="GB Automation"
            className="relative z-10 h-9 w-9 object-contain"
          />
        </div>
      </Link>

      {tabs.map(({ to, end, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }: { isActive: boolean }): string =>
            cn(
              'hover-mini flex items-center gap-2 px-3 py-3 text-[11px] font-medium uppercase tracking-widest border-b-2 transition-colors',
              isActive
                ? 'border-primary text-primary'
                : 'border-transparent text-text-tertiary hover:text-primary'
            )
          }
        >
          <Icon className="h-4 w-4" />
          {label}
          {to === '/dashboard' && hasRunning && (
            <span className="flex h-2 w-2 rounded-full bg-primary animate-pulse" />
          )}
        </NavLink>
      ))}
      <span className="ml-auto text-[10px] uppercase tracking-widest text-text-tertiary">
        v{import.meta.env.VITE_APP_VERSION as string}
        {updateCheck?.updateAvailable && updateCheck.releaseUrl && (
          <a
            href={updateCheck.releaseUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-1.5 inline-flex items-center gap-1 text-[10px] text-primary hover:underline"
            title={`v${updateCheck.latestVersion} available`}
          >
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />v
            {updateCheck.latestVersion}
          </a>
        )}
      </span>
    </nav>
  );
}
