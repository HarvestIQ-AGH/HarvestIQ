"use client"

import { useEffect, useRef, useState, useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Check, ArrowRight, Users, Zap, Gift } from "lucide-react"
import { useLanguage } from "@/lib/language-context"

interface WaitlistSectionProps {
  onSectionVisible: () => void
}

export function WaitlistSection({ onSectionVisible }: WaitlistSectionProps) {
  const { t } = useLanguage()
  const sectionRef = useRef<HTMLElement>(null)
  const [email, setEmail] = useState("")
  const [cropType, setCropType] = useState("")
  const [farmSize, setFarmSize] = useState("")
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const benefits = useMemo(
    () => [
      {
        icon: Zap,
        title: t.waitlist.benefitEarlyTitle,
        description: t.waitlist.benefitEarlyDesc,
      },
      {
        icon: Gift,
        title: t.waitlist.benefitPricingTitle,
        description: t.waitlist.benefitPricingDesc,
      },
      {
        icon: Users,
        title: t.waitlist.benefitShapeTitle,
        description: t.waitlist.benefitShapeDesc,
      },
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return

    setIsLoading(true)

    await new Promise((resolve) => setTimeout(resolve, 1500))

    setIsLoading(false)
    setIsSubmitted(true)
  }

  return (
    <section ref={sectionRef} id="waitlist" className="py-24 bg-background relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent" />

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground text-balance">
              {t.waitlist.pageTitle}
            </h2>
            <p className="mt-4 text-lg text-muted-foreground text-pretty leading-relaxed">
              {t.waitlist.pageDescription}
            </p>

            <div className="mt-10 space-y-6">
              {benefits.map((benefit) => (
                <div key={benefit.title} className="flex items-start gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 shrink-0">
                    <benefit.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">{benefit.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{benefit.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <Card className="shadow-xl border-2">
              <CardContent className="p-8">
                {!isSubmitted ? (
                  <>
                    <div className="text-center mb-8">
                      <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-primary/10 mb-4">
                        <ArrowRight className="h-7 w-7 text-primary" />
                      </div>
                      <h3 className="text-xl font-semibold text-foreground">{t.waitlist.formTitle}</h3>
                      <p className="mt-2 text-sm text-muted-foreground">{t.waitlist.formSubtitle}</p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">
                          {t.waitlist.emailLabel} <span className="text-destructive">*</span>
                        </label>
                        <Input
                          type="email"
                          placeholder={t.waitlist.emailPlaceholder}
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          required
                          className="h-11"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">
                          {t.waitlist.cropTypeLabel}
                        </label>
                        <Input
                          type="text"
                          placeholder={t.waitlist.cropTypePlaceholder}
                          value={cropType}
                          onChange={(e) => setCropType(e.target.value)}
                          className="h-11"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">
                          {t.waitlist.farmSizeLabel}
                        </label>
                        <Input
                          type="number"
                          placeholder={t.waitlist.farmSizePlaceholder}
                          value={farmSize}
                          onChange={(e) => setFarmSize(e.target.value)}
                          className="h-11"
                        />
                      </div>

                      <Button
                        type="submit"
                        size="lg"
                        className="w-full mt-6 h-12 text-base"
                        disabled={isLoading || !email}
                      >
                        {isLoading ? (
                          <span className="flex items-center gap-2">
                            <span className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                            {t.waitlist.joining}
                          </span>
                        ) : (
                          <>
                            {t.waitlist.joinWaitlist}
                            <ArrowRight className="ml-2 h-5 w-5" />
                          </>
                        )}
                      </Button>

                      <p className="text-xs text-center text-muted-foreground mt-4">
                        {t.waitlist.privacyLine1}
                        <br />
                        {t.waitlist.privacyLine2}
                      </p>
                    </form>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-primary/10 mb-6">
                      <Check className="h-8 w-8 text-primary" />
                    </div>
                    <h3 className="text-xl font-semibold text-foreground">{t.waitlist.successTitle}</h3>
                    <p className="mt-3 text-muted-foreground max-w-sm mx-auto">{t.waitlist.successMessage}</p>
                    <Button
                      variant="outline"
                      className="mt-6"
                      onClick={() => {
                        setIsSubmitted(false)
                        setEmail("")
                        setCropType("")
                        setFarmSize("")
                      }}
                    >
                      {t.waitlist.signUpAnother}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  )
}
