import "./globals.css";

export const metadata = {
  title: "NyayaSetu AI + ZamanatAI",
  description: "Google Maps for Justice: civic-tech legal aid workflows for Indian citizens."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
