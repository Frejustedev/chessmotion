import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChessMotion – Chess to Video",
  description: "Convert chess games (PGN, Lichess, Chess.com) into MP4 videos or GIFs.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-surface antialiased">{children}</body>
    </html>
  );
}
