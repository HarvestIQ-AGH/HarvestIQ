"use client"

import { useState } from "react"
import { Header } from "@/components/header"
import { HeroSection } from "@/components/hero-section"
import { FeaturesSection } from "@/components/features-section"
import { HowItWorksSection } from "@/components/how-it-works-section"
import { DashboardPreview } from "@/components/dashboard-preview"
import { AlertsSection } from "@/components/alerts-section"
import { DataInputSection } from "@/components/data-input-section"
import { FarmMapSection } from "@/components/farm-map-section"
import { WaitlistSection } from "@/components/waitlist-section"
import { Footer } from "@/components/footer"

export default function Home() {
  const [activeSection, setActiveSection] = useState<string>("hero")

  return (
    <main className="min-h-screen">
      <Header activeSection={activeSection} />
      <HeroSection onSectionVisible={() => setActiveSection("hero")} />
      <FeaturesSection onSectionVisible={() => setActiveSection("features")} />
      <HowItWorksSection onSectionVisible={() => setActiveSection("how-it-works")} />
      <DashboardPreview onSectionVisible={() => setActiveSection("dashboard")} />
      <FarmMapSection />
      <DataInputSection onSectionVisible={() => setActiveSection("data-input")} />
      <AlertsSection onSectionVisible={() => setActiveSection("alerts")} />
      <WaitlistSection onSectionVisible={() => setActiveSection("waitlist")} />
      <Footer />
    </main>
  )
}
