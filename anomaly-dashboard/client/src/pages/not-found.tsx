import { Link } from "wouter";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
      <div className="text-5xl font-bold tabular-nums text-muted-foreground/30">404</div>
      <div className="text-sm text-muted-foreground">Page not found</div>
      <Link href="/" className="text-xs text-primary hover:underline">Go to Overview</Link>
    </div>
  );
}
