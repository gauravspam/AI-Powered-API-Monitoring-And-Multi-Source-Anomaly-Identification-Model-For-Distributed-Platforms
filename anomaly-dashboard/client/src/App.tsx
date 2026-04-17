import { Switch, Route, Router, Link, useLocation } from "wouter";
import { useHashLocation } from "wouter/use-hash-location";
import { queryClient } from "@/lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useState, useEffect } from "react";
import {
  LayoutDashboard, Server, Bell, FileText, Cpu, GitBranch,
  Zap, Moon, Sun, Menu, X, Activity, ChevronRight
} from "lucide-react";

// Pages
import DashboardPage from "@/pages/Dashboard";
import ServicesPage from "@/pages/Services";
import AlertsPage from "@/pages/Alerts";
import LogsPage from "@/pages/Logs";
import TracesPage from "@/pages/Traces";
import ModelsPage from "@/pages/Models";
import SimulatorPage from "@/pages/Simulator";
import NotFound from "@/pages/not-found";

const navItems = [
  { path: "/", label: "Overview", icon: LayoutDashboard },
  { path: "/services", label: "Services", icon: Server },
  { path: "/alerts", label: "Alerts", icon: Bell },
  { path: "/logs", label: "Logs", icon: FileText },
  { path: "/traces", label: "Traces", icon: GitBranch },
  { path: "/models", label: "ML Models", icon: Cpu },
  { path: "/simulator", label: "Simulator", icon: Zap },
];

function Sidebar({ dark, setDark, collapsed, setCollapsed }: {
  dark: boolean;
  setDark: (v: boolean) => void;
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
}) {
  const [location] = useLocation();

  return (
    <aside
      className="flex flex-col h-full border-r border-border bg-sidebar transition-all duration-200"
      style={{ width: collapsed ? "56px" : "220px", background: "hsl(var(--sidebar-background))" }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-3.5 border-b border-sidebar-border min-h-[52px]">
        <div className="shrink-0">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-label="Anomaly Monitor">
            <rect width="28" height="28" rx="6" fill="hsl(188, 80%, 42%)" opacity="0.15"/>
            <path d="M4 20 L9 12 L14 16 L18 8 L24 20" stroke="hsl(188, 80%, 42%)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <circle cx="18" cy="8" r="2.5" fill="hsl(188, 80%, 42%)"/>
            <circle cx="9" cy="12" r="1.5" fill="hsl(188, 80%, 42%)" opacity="0.6"/>
          </svg>
        </div>
        {!collapsed && (
          <div>
            <div className="text-xs font-bold tracking-wider text-sidebar-foreground uppercase leading-none">AnomalyIQ</div>
            <div className="text-[10px] text-muted-foreground mt-0.5 leading-none">API Monitor</div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto text-muted-foreground hover:text-sidebar-foreground transition-colors"
          data-testid="button-collapse-sidebar"
        >
          {collapsed ? <ChevronRight size={14} /> : <Menu size={14} />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-2 overflow-y-auto overscroll-contain">
        {navItems.map(({ path, label, icon: Icon }) => {
          const isActive = location === path || (path !== "/" && location.startsWith(path));
          return (
            <Link
              key={path}
              href={path}
              className={`flex items-center gap-3 px-3 py-2 mx-2 my-0.5 rounded-md text-sm transition-all duration-150 ${
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              }`}
              data-testid={`nav-${label.toLowerCase().replace(/\s/g, "-")}`}
            >
              <Icon size={15} className={isActive ? "text-primary" : ""} />
              {!collapsed && <span className="truncate">{label}</span>}
              {!collapsed && path === "/alerts" && (
                <span className="ml-auto text-[10px] font-mono badge-critical rounded px-1.5 py-0.5">5</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom actions */}
      <div className="border-t border-sidebar-border p-2">
        <button
          onClick={() => setDark(!dark)}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sidebar-foreground hover:bg-sidebar-accent transition-colors text-sm"
          data-testid="button-theme-toggle"
          aria-label="Toggle theme"
        >
          {dark ? <Sun size={15} /> : <Moon size={15} />}
          {!collapsed && <span>{dark ? "Light Mode" : "Dark Mode"}</span>}
        </button>
      </div>
    </aside>
  );
}

function TopBar({ title }: { title?: string }) {
  const [location] = useLocation();
  const page = navItems.find(n => n.path === location || (n.path !== "/" && location.startsWith(n.path)));
  const pageLabel = page?.label || title || "Overview";

  return (
    <header className="flex items-center justify-between px-5 border-b border-border bg-card/80 backdrop-blur-sm min-h-[52px]">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-foreground">{pageLabel}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500 status-dot-live"></span>
          <span>Live</span>
        </div>
        <div className="text-xs text-muted-foreground tabular-nums hidden sm:block" id="topbar-time">
          {new Date().toLocaleTimeString()}
        </div>
      </div>
    </header>
  );
}

function AppShell({ children }: { children: React.ReactNode }) {
  const [dark, setDark] = useState(true);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.remove("light");
    } else {
      document.documentElement.classList.add("light");
    }
  }, [dark]);

  // Update clock
  useEffect(() => {
    const el = document.getElementById("topbar-time");
    const interval = setInterval(() => {
      if (el) el.textContent = new Date().toLocaleTimeString();
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-layout">
      <Sidebar dark={dark} setDark={setDark} collapsed={collapsed} setCollapsed={setCollapsed} />
      <div className="dashboard-main overflow-hidden">
        <TopBar />
        <div className="dashboard-content">
          {children}
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Router hook={useHashLocation}>
          <AppShell>
            <Switch>
              <Route path="/" component={DashboardPage} />
              <Route path="/services" component={ServicesPage} />
              <Route path="/alerts" component={AlertsPage} />
              <Route path="/logs" component={LogsPage} />
              <Route path="/traces" component={TracesPage} />
              <Route path="/models" component={ModelsPage} />
              <Route path="/simulator" component={SimulatorPage} />
              <Route component={NotFound} />
            </Switch>
          </AppShell>
        </Router>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
