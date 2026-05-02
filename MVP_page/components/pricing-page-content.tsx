"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Mail, MessageCircle } from "lucide-react"
import { useLanguage } from "@/lib/language-context"

export function PricingPageContent() {
  const { t } = useLanguage()
  const p = t.pages.pricing

  return (
    <main className="flex-1">
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl text-balance">
          {p.title}
        </h1>
        <p className="mt-4 text-lg text-muted-foreground leading-relaxed">{p.lead}</p>
        <p className="mt-6 text-muted-foreground leading-relaxed">
          <span className="font-medium text-foreground">{p.privateLead}</span> {p.privateBody}
        </p>

        <ul className="mt-10 space-y-3 text-sm text-muted-foreground border-l-2 border-primary/30 pl-6">
          <li>{p.bullet1}</li>
          <li>{p.bullet2}</li>
          <li>{p.bullet3}</li>
        </ul>

        <div className="mt-12 flex flex-col gap-4 sm:flex-row sm:flex-wrap">
          <Button size="lg" className="w-full sm:w-auto" asChild>
            <Link href="/contact">
              <Mail className="mr-2 h-5 w-5" />
              {p.ctaQuote}
            </Link>
          </Button>
          <Button size="lg" variant="outline" className="w-full sm:w-auto" asChild>
            <Link href="/#waitlist">
              <MessageCircle className="mr-2 h-5 w-5" />
              {p.ctaWaitlist}
            </Link>
          </Button>
        </div>

        <p className="mt-10 text-sm text-muted-foreground">
          {p.footnoteBefore}{" "}
          <Link href="/contact" className="font-medium text-primary underline-offset-4 hover:underline">
            {p.contactLink}
          </Link>{" "}
          {p.footnoteAfter}
        </p>
      </div>
    </main>
  )
}
