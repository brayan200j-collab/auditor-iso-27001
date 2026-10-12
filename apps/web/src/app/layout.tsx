import type { Metadata } from "next";
import { Poppins } from "next/font/google";
import { headers } from "next/headers";

import { brand, common } from "@/content/es";

import "./globals.css";

// Self-hosted at build time by Next.js: no requests to Google from the browser (CSP font-src 'self').
const poppins = Poppins({
  subsets: ["latin", "latin-ext"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
  variable: "--font-poppins",
});

export const metadata: Metadata = {
  title: { default: brand.name, template: `%s · ${brand.name}` },
  description: brand.tagline,
  robots: { index: false, follow: false },
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  // Reading the request makes every page dynamic, so each response gets its own CSP nonce.
  await headers();
  return (
    <html lang="es" className={`${poppins.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <a
          href="#contenido"
          className="focus:bg-surface sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:px-4 focus:py-2"
        >
          {common.skipToContent}
        </a>
        {children}
      </body>
    </html>
  );
}
