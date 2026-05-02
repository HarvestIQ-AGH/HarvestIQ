"use client"

import Link from "next/link"
import { useLanguage } from "@/lib/language-context"

export function AboutPageContent() {
  const { t } = useLanguage()
  const a = t.pages.about

  return (
    <main className="flex-1">
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl text-balance">
          {a.title}
        </h1>
        <div className="mt-10 space-y-6 text-muted-foreground leading-relaxed">
          <p>{a.p1}</p>
          <p>{a.p2}</p>
          <p>
            {a.p3Before}
            <Link href="/contact" className="font-medium text-primary underline-offset-4 hover:underline">
              {a.contactLink}
            </Link>
            {a.p3After}
          </p>
        </div>
      </div>
    </main>
  )
}
