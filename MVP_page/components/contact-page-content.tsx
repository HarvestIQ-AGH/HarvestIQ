"use client"

import Link from "next/link"
import { Mail, Phone } from "lucide-react"
import { useLanguage } from "@/lib/language-context"

const PROJECT_EMAIL = "contact@example.com"
const PROJECT_PHONE = "+48 123 456 789"

export function ContactPageContent() {
  const { t } = useLanguage()
  const c = t.pages.contact

  return (
    <main className="flex-1">
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl text-balance">
          {c.title}
        </h1>
        <p className="mt-4 text-lg text-muted-foreground leading-relaxed">{c.intro}</p>

        <ul className="mt-12 space-y-6 border-t border-border pt-10">
          {c.roles.map((role, index) => (
            <li
              key={`${role}-${index}`}
              className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-8"
            >
              <span className="font-semibold text-foreground">{c.teamMemberName}</span>
              <span className="text-sm text-muted-foreground">{role}</span>
            </li>
          ))}
        </ul>

        <div className="mt-12 rounded-2xl border border-border bg-card p-8">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            {c.projectContact}
          </h2>
          <div className="mt-6 space-y-4">
            <a
              href={`mailto:${PROJECT_EMAIL}`}
              className="flex items-center gap-3 text-foreground transition-colors hover:text-primary"
            >
              <Mail className="h-5 w-5 shrink-0 text-primary" />
              <span>{PROJECT_EMAIL}</span>
            </a>
            <a
              href={`tel:${PROJECT_PHONE.replace(/\s/g, "")}`}
              className="flex items-center gap-3 text-foreground transition-colors hover:text-primary"
            >
              <Phone className="h-5 w-5 shrink-0 text-primary" />
              <span>{PROJECT_PHONE}</span>
            </a>
          </div>
          <p className="mt-6 text-sm text-muted-foreground">
            {c.hintBeforeHome}{" "}
            <Link href="/" className="font-medium text-primary underline-offset-4 hover:underline">
              {c.returnHome}
            </Link>{" "}
            {c.hintOrWaitlist}{" "}
            <Link href="/#waitlist" className="font-medium text-primary underline-offset-4 hover:underline">
              {c.waitlistWord}
            </Link>
            .
          </p>
        </div>
      </div>
    </main>
  )
}
