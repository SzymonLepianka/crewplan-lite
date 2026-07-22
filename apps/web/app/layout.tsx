import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CrewPlan Lite",
  description: "Edukacyjny projekt harmonogramowania ekip",
};

type RootLayoutProps = {
  children: React.ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="pl">
      <body>{children}</body>
    </html>
  );
}
