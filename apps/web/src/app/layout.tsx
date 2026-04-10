import type { Metadata, Viewport } from "next";
import { Inter, Instrument_Serif } from "next/font/google";
import { ThemeProvider } from "@/lib/theme";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
});

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  weight: "400",
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: {
    default: "HireIQ — AI Resume Screening & Candidate Ranking",
    template: "%s — HireIQ",
  },
  description:
    "Rank candidates against your job description in 30 seconds. Evidence-backed scoring, side-by-side comparison, and skills gap analysis. Free to start.",
  keywords: [
    "AI resume screening", "candidate ranking", "hiring tool", "recruitment software",
    "resume parser", "job description matching", "candidate scoring", "shortlisting tool",
    "recruiter software", "HR tech", "evidence-based hiring", "AI recruitment",
  ],
  authors: [{ name: "HireIQ", url: "https://hireiq.domato.ai" }],
  creator: "Domato AI",
  publisher: "Domato AI Pty Ltd",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: "/icon-192.png",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  metadataBase: new URL("https://hireiq.domato.ai"),
  alternates: {
    canonical: "https://hireiq.domato.ai",
  },
  openGraph: {
    type: "website",
    locale: "en_AU",
    url: "https://hireiq.domato.ai",
    siteName: "HireIQ",
    title: "HireIQ — AI Resume Screening & Candidate Ranking",
    description: "Rank candidates against your job description in 30 seconds. Evidence-backed scoring, side-by-side comparison, and skills gap analysis.",
    images: [
      {
        url: "https://sthireiqdevaue.blob.core.windows.net/videos/hireiq-demo-poster.jpg",
        width: 1200,
        height: 630,
        alt: "HireIQ - AI-powered candidate ranking",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "HireIQ — AI Resume Screening & Candidate Ranking",
    description: "Rank candidates against your job description in 30 seconds. Free to start.",
    images: ["https://sthireiqdevaue.blob.core.windows.net/videos/hireiq-demo-poster.jpg"],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f5f0eb",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${instrumentSerif.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `try{document.documentElement.dataset.theme=localStorage.getItem('hireiq-theme')||'dark'}catch(e){}` }} />
      </head>
      <body className="antialiased">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
