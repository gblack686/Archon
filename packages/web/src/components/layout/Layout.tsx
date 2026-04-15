import { Outlet } from 'react-router';
import { TopNav } from './TopNav';

export function Layout(): React.ReactElement {
  return (
    <div className="ambient-glow flex h-screen flex-col bg-background">
      <TopNav />
      <main className="relative z-10 flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
