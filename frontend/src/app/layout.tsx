import type { Metadata } from "next";
import { Montserrat, Inter, Fraunces, Outfit, DM_Mono } from "next/font/google";
import "./globals.css";

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800"],
  display: "swap",
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const dmMono = DM_Mono({
  variable: "--font-dm-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "CRI Guelmim-Oued Noun - Portail Numérique Intelligent",
  description:
    "Guichet unique régional et assistant intelligent pour l'accompagnement des investisseurs dans la région Guelmim-Oued Noun",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
      className={`${fraunces.variable} ${outfit.variable} ${dmMono.variable} ${montserrat.variable} ${inter.variable}`}
    >
      <body style={{ fontFamily: "var(--font-outfit), var(--font-inter), sans-serif", backgroundColor: "#F4EDE3", color: "#1C1610", margin: 0 }}>
        {children}
      </body>
    </html>
  );
}