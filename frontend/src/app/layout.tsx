import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TimeJump AI",
  description: "Search Microsoft Teams meeting recordings by topic and jump to the moment.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
