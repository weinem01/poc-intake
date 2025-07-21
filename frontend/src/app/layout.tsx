import type { Metadata } from "next";
import { Lexend, Noto_Sans } from "next/font/google";
import "./globals.css";

const lexend = Lexend({
  variable: "--font-lexend",
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
});

const notoSans = Noto_Sans({
  variable: "--font-noto-sans",
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
});

export const metadata: Metadata = {
  title: "Pound of Cure - Patient Intake",
  description: "Patient intake form for Pound of Cure Weight Loss",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.gstatic.com/" crossOrigin="" />
      </head>
      <body
        className={`${lexend.variable} ${notoSans.variable} antialiased`}
        style={{fontFamily: 'Lexend, "Noto Sans", sans-serif'}}
        suppressHydrationWarning={true}
      >
        {children}
      </body>
    </html>
  );
}
