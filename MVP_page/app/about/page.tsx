import type { Metadata } from "next"
import { SubpageHeader } from "@/components/subpage-header"
import { Footer } from "@/components/footer"
import { AboutPageContent } from "@/components/about-page-content"

export const metadata: Metadata = {
  title: "About Us | HarvestIQ",
  description:
    "HarvestIQ is a student-built project helping farmers make data-driven decisions with AI and field analytics.",
}

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <SubpageHeader />
      <AboutPageContent />
      <Footer />
    </div>
  )
}
