"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useLanguage } from "@/lib/language-context"
import {
  Bell,
  Droplets,
  Leaf,
  CloudRain,
  Sun,
  AlertTriangle,
  Check,
  Calendar,
  Clock,
} from "lucide-react"

interface AlertsSectionProps {
  onSectionVisible: () => void
}

export function AlertsSection({ onSectionVisible }: AlertsSectionProps) {
  const { t, language } = useLanguage()
  const sectionRef = useRef<HTMLElement>(null)
  const [dismissedAlerts, setDismissedAlerts] = useState<number[]>([])

  const demoAlerts = useMemo(
    () => [
      {
        id: 1,
        type: "water" as const,
        icon: Droplets,
        title: t.alerts.demoAlert1Title,
        message: t.alerts.demoAlert1Message,
        time: t.alerts.demoTime2h,
        priority: "medium" as const,
        color: "text-blue-600",
        bgColor: "bg-blue-100",
      },
      {
        id: 2,
        type: "fertilizer" as const,
        icon: Leaf,
        title: t.alerts.demoAlert2Title,
        message: t.alerts.demoAlert2Message,
        time: t.alerts.demoTime5h,
        priority: "low" as const,
        color: "text-primary",
        bgColor: "bg-primary/10",
      },
      {
        id: 3,
        type: "weather" as const,
        icon: CloudRain,
        title: t.alerts.demoAlert3Title,
        message: t.alerts.demoAlert3Message,
        time: t.alerts.demoTime1d,
        priority: "high" as const,
        color: "text-amber-600",
        bgColor: "bg-amber-100",
      },
      {
        id: 4,
        type: "pest" as const,
        icon: AlertTriangle,
        title: t.alerts.demoAlert4Title,
        message: t.alerts.demoAlert4Message,
        time: t.alerts.demoTime1d,
        priority: "high" as const,
        color: "text-red-600",
        bgColor: "bg-red-100",
      },
      {
        id: 5,
        type: "growth" as const,
        icon: Sun,
        title: t.alerts.demoAlert5Title,
        message: t.alerts.demoAlert5Message,
        time: t.alerts.demoTime2d,
        priority: "low" as const,
        color: "text-chart-4",
        bgColor: "bg-chart-4/20",
      },
    ],
    [language]
  )

  const scheduleItems = useMemo(
    () => [
      {
        day: t.alerts.today,
        tasks: [t.alerts.scheduleToday1, t.alerts.scheduleToday2],
      },
      {
        day: t.alerts.tomorrow,
        tasks: [t.alerts.scheduleTomorrow1, t.alerts.scheduleTomorrow2],
      },
      {
        day: t.alerts.thisWeek,
        tasks: [t.alerts.scheduleWeek1, t.alerts.scheduleWeek2],
      },
    ],
    [language]
  )

  useEffect(() => {
    setDismissedAlerts([])
  }, [language])

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

  const dismissAlert = (id: number) => {
    setDismissedAlerts((prev) => [...prev, id])
  }

  const activeAlerts = demoAlerts.filter((alert) => !dismissedAlerts.includes(alert.id))

  return (
    <section ref={sectionRef} id="alerts" className="py-24 bg-muted/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground text-balance">
            {t.alerts.sectionTitle}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            {t.alerts.sectionDescription}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <Bell className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground">{t.alerts.recentAlertsTitle}</h3>
                  <p className="text-sm text-muted-foreground">
                    {t.alerts.activeNotifications.replace("{count}", String(activeAlerts.length))}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm">
                {t.alerts.markAllRead}
              </Button>
            </div>

            <div className="space-y-4">
              {activeAlerts.map((alert) => (
                <Card
                  key={alert.id}
                  className={`transition-all duration-300 hover:shadow-md ${
                    alert.priority === "high" ? "border-l-4 border-l-amber-500" : ""
                  }`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${alert.bgColor} shrink-0`}>
                        <alert.icon className={`h-5 w-5 ${alert.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <h4 className="font-medium text-foreground">{alert.title}</h4>
                            <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                              {alert.message}
                            </p>
                            <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              {alert.time}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => dismissAlert(alert.id)}
                            className="shrink-0"
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {activeAlerts.length === 0 && (
                <Card>
                  <CardContent className="p-8 text-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 mx-auto mb-4">
                      <Check className="h-6 w-6 text-primary" />
                    </div>
                    <h4 className="font-medium text-foreground">{t.alerts.allCaughtUp}</h4>
                    <p className="mt-1 text-sm text-muted-foreground">{t.alerts.noActiveAlerts}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/30">
                <Calendar className="h-5 w-5 text-accent-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-foreground">{t.alerts.upcomingTasks}</h3>
                <p className="text-sm text-muted-foreground">{t.alerts.scheduleSubtitle}</p>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                {scheduleItems.map((item, index) => (
                  <div
                    key={item.day}
                    className={`p-4 ${index !== scheduleItems.length - 1 ? "border-b border-border" : ""}`}
                  >
                    <h4 className="text-sm font-semibold text-foreground mb-3">{item.day}</h4>
                    <ul className="space-y-2">
                      {item.tasks.map((task, taskIndex) => (
                        <li key={taskIndex} className="flex items-start gap-2">
                          <div className="h-1.5 w-1.5 rounded-full bg-primary mt-2 shrink-0" />
                          <span className="text-sm text-muted-foreground">{task}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardContent className="p-4">
                <h4 className="font-medium text-foreground mb-2">{t.alerts.alertPreferencesTitle}</h4>
                <p className="text-sm text-muted-foreground mb-4">{t.alerts.alertPreferencesDesc}</p>
                <Button variant="outline" size="sm" className="w-full">
                  {t.alerts.configureAlerts}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  )
}
