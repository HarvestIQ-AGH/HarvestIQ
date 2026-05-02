import type { Metadata } from "next"
import { SubpageHeader } from "@/components/subpage-header"
import { Footer } from "@/components/footer"
import { PricingPageContent } from "@/components/pricing-page-content"

export const metadata: Metadata = {
  title: "Pricing | HarvestIQ",
  description:
    "HarvestIQ pricing is tailored to your farm. Contact us for a private quote.",
}

export default function PricingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <SubpageHeader />
      <PricingPageContent />
      <Footer />
    </div>
  )
}
