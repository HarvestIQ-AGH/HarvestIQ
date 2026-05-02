"use client"

import { useEffect, useRef, useMemo } from "react"
import { Upload, Cpu, BarChart3, Bell } from "lucide-react"
import { useLanguage } from "@/lib/language-context"

interface HowItWorksSectionProps {
  onSectionVisible: () => void
}

export function HowItWorksSection({ onSectionVisible }: HowItWorksSectionProps) {
  const { t } = useLanguage()
  const sectionRef = useRef<HTMLElement>(null)

  const steps = useMemo(
    () => [
      { icon: Upload, step: "01", title: t.howItWorks.step1, description: t.howItWorks.step1Desc },
      { icon: Cpu, step: "02", title: t.howItWorks.step2, description: t.howItWorks.step2Desc },
      {
        icon: BarChart3,
        step: "03",
        title: t.howItWorks.step3,
        description: t.howItWorks.step3Desc,
      },
      { icon: Bell, step: "04", title: t.howItWorks.step4, description: t.howItWorks.step4Desc },
    ],
    [t]
  )

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          onSectionVisible()
        }
      },
      { threshold: 0.3 }
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => observer.disconnect()
  }, [onSectionVisible])

  return (
    <section ref={sectionRef} id="how-it-works" className="py-24 bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground text-balance">
            {t.howItWorks.title}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            {t.howItWorks.description}
          </p>
        </div>

        <div className="relative">
          <div
            className="hidden lg:block absolute left-0 right-0 top-[2.5rem] h-0.5 bg-border z-0 pointer-events-none"
            aria-hidden
          />

          <div className="relative z-[1] grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={step.step} className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="relative z-10 flex h-20 w-20 items-center justify-center rounded-2xl bg-card border-2 border-primary shadow-lg">
                    <step.icon className="h-8 w-8 text-primary" />
                  </div>

                  <div className="absolute top-6 left-1/2 -translate-x-1/2 flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                    {index + 1}
                  </div>

                  <h3 className="mt-6 text-xl font-semibold text-foreground">{step.title}</h3>
                  <p className="mt-3 text-muted-foreground text-sm leading-relaxed max-w-xs">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
