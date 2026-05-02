import type { Metadata } from "next"
import { SubpageHeader } from "@/components/subpage-header"
import { Footer } from "@/components/footer"
import { ContactPageContent } from "@/components/contact-page-content"

export const metadata: Metadata = {
  title: "Contact | HarvestIQ",
  description: "Reach the HarvestIQ student team.",
}

export default function ContactPage() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <SubpageHeader />
      <ContactPageContent />
      <Footer />
    </div>
  )
}
