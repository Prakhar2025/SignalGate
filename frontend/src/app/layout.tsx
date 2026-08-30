import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SignalGate - research-integrity gate for candidate trading signals",
  description:
    "Every candidate signal is investigated like a fraud case: statistical probes, verdicts with receipts, silence unless a signal deserves a researcher's hour.",
};

function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="glow-signal inline-flex h-7 w-7 items-center justify-center rounded-md bg-signal/10 font-mono text-xs font-bold text-signal">
            SG
          </span>
          <span className="font-semibold tracking-tight">SignalGate</span>
          <span className="rounded-full border border-line px-2 py-0.5 font-mono text-[10px] text-muted">
            v0.1
          </span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          <Link
            href="/gate"
            className="rounded-md px-3 py-1.5 text-muted transition-colors hover:bg-surface hover:text-ink"
          >
            Gate
          </Link>
          <Link
            href="/digest"
            className="rounded-md px-3 py-1.5 text-muted transition-colors hover:bg-surface hover:text-ink"
          >
            Digest
          </Link>
          <Link
            href="/evaluation"
            className="rounded-md px-3 py-1.5 text-muted transition-colors hover:bg-surface hover:text-ink"
          >
            Evaluation
          </Link>
          <Link
            href="/gate"
            className="ml-2 rounded-md bg-signal px-3.5 py-1.5 font-medium text-background transition-colors hover:bg-signal-dim"
          >
            Screen a signal
          </Link>
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-24 border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-xs text-dim sm:flex-row sm:items-center sm:justify-between">
        <span>Verdicts are advisory. The researcher decides. SignalGate recommends, never trades.</span>
        <span className="font-mono">
          100% synthetic data · zero keys in LOCAL_MOCK · receipts for every run
        </span>
      </div>
    </footer>
  );
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="grain flex min-h-full flex-col">
        <Nav />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
