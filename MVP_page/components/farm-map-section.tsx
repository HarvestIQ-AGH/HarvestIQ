"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  MapPin,
  Pencil,
  Trash2,
  Layers,
  Droplets,
  Leaf,
  MousePointer2,
  Undo2,
  Check,
  X,
  Satellite,
  Map,
  ZoomIn,
  ZoomOut,
  LocateFixed,
  FlaskConical,
} from "lucide-react"
import dynamic from "next/dynamic"
import { useLanguage } from "@/lib/language-context"
import { translations, type Translations } from "@/lib/translations"

// Dynamically import Leaflet components to avoid SSR issues
const MapContainer = dynamic(
  () => import("react-leaflet").then((mod) => mod.MapContainer),
  { ssr: false }
)
const TileLayer = dynamic(
  () => import("react-leaflet").then((mod) => mod.TileLayer),
  { ssr: false }
)
const Polygon = dynamic(
  () => import("react-leaflet").then((mod) => mod.Polygon),
  { ssr: false }
)
const Marker = dynamic(
  () => import("react-leaflet").then((mod) => mod.Marker),
  { ssr: false }
)
const Popup = dynamic(
  () => import("react-leaflet").then((mod) => mod.Popup),
  { ssr: false }
)

const CROP_KEYS = ["corn", "wheat", "soybeans", "rice", "cotton", "barley", "oats", "alfalfa"] as const
type CropKey = (typeof CROP_KEYS)[number]

interface FieldData {
  id: string
  name: string
  coordinates: [number, number][]
  color: string
  fillColor: string
  cropType: CropKey
  soilMoisture: number
  soilPH: number
  nitrogen: number
  area: number
  lastUpdated: string
}

const FIELD_COLORS = [
  { stroke: "#16a34a", fill: "rgba(22, 163, 74, 0.35)" },
  { stroke: "#2563eb", fill: "rgba(37, 99, 235, 0.35)" },
  { stroke: "#ea580c", fill: "rgba(234, 88, 12, 0.35)" },
  { stroke: "#9333ea", fill: "rgba(147, 51, 234, 0.35)" },
  { stroke: "#0891b2", fill: "rgba(8, 145, 178, 0.35)" },
]

// Sample farm location (Iowa farmland)
const FARM_CENTER: [number, number] = [41.878, -93.097]

function buildInitialFields(t: Translations): FieldData[] {
  return [
    {
      id: "field-1",
      name: t.farmMap.demoFieldNorth,
      coordinates: [
        [41.884, -93.108],
        [41.884, -93.095],
        [41.879, -93.095],
        [41.879, -93.108],
      ],
      color: FIELD_COLORS[0].stroke,
      fillColor: FIELD_COLORS[0].fill,
      cropType: "corn",
      soilMoisture: 68,
      soilPH: 6.5,
      nitrogen: 45,
      area: 42.5,
      lastUpdated: t.farmMap.demoUpdated2h,
    },
    {
      id: "field-2",
      name: t.farmMap.demoFieldEast,
      coordinates: [
        [41.879, -93.094],
        [41.879, -93.082],
        [41.873, -93.082],
        [41.873, -93.094],
      ],
      color: FIELD_COLORS[1].stroke,
      fillColor: FIELD_COLORS[1].fill,
      cropType: "wheat",
      soilMoisture: 52,
      soilPH: 7.0,
      nitrogen: 38,
      area: 38.2,
      lastUpdated: t.farmMap.demoUpdated5h,
    },
    {
      id: "field-3",
      name: t.farmMap.demoFieldSouth,
      coordinates: [
        [41.872, -93.105],
        [41.872, -93.092],
        [41.867, -93.092],
        [41.867, -93.105],
      ],
      color: FIELD_COLORS[2].stroke,
      fillColor: FIELD_COLORS[2].fill,
      cropType: "soybeans",
      soilMoisture: 74,
      soilPH: 6.8,
      nitrogen: 52,
      area: 55.8,
      lastUpdated: t.farmMap.demoUpdated1d,
    },
  ]
}

// Map click handler component
function MapClickHandler({
  onMapClick,
  drawMode,
}: {
  onMapClick: (lat: number, lng: number) => void
  drawMode: "select" | "draw"
}) {
  const [MapEventsComponent, setMapEventsComponent] = useState<any>(null)

  useEffect(() => {
    import("react-leaflet").then((mod) => {
      const MapEvents = () => {
        mod.useMapEvents({
          click: (e: any) => {
            if (drawMode === "draw") {
              onMapClick(e.latlng.lat, e.latlng.lng)
            }
          },
        })
        return null
      }
      setMapEventsComponent(() => MapEvents)
    })
  }, [drawMode, onMapClick])

  if (!MapEventsComponent) return null
  return <MapEventsComponent />
}

// Map controller for zoom and center
function MapController({
  mapRef,
  onZoomIn,
  onZoomOut,
  onRecenter,
}: {
  mapRef: React.MutableRefObject<any>
  onZoomIn: () => void
  onZoomOut: () => void
  onRecenter: () => void
}) {
  return (
    <div className="absolute top-4 right-4 z-[1000] flex flex-col gap-2">
      <Button
        size="icon"
        variant="secondary"
        className="h-9 w-9 shadow-lg bg-card hover:bg-muted"
        onClick={onZoomIn}
      >
        <ZoomIn className="h-4 w-4" />
      </Button>
      <Button
        size="icon"
        variant="secondary"
        className="h-9 w-9 shadow-lg bg-card hover:bg-muted"
        onClick={onZoomOut}
      >
        <ZoomOut className="h-4 w-4" />
      </Button>
      <Button
        size="icon"
        variant="secondary"
        className="h-9 w-9 shadow-lg bg-card hover:bg-muted"
        onClick={onRecenter}
      >
        <LocateFixed className="h-4 w-4" />
      </Button>
    </div>
  )
}

export function FarmMapSection() {
  const { t, language } = useLanguage()
  const [fields, setFields] = useState<FieldData[]>(() => buildInitialFields(translations.en))
  const [selectedField, setSelectedField] = useState<FieldData | null>(null)
  const [drawMode, setDrawMode] = useState<"select" | "draw">("select")
  const [currentPoints, setCurrentPoints] = useState<[number, number][]>([])
  const [editingFieldData, setEditingFieldData] = useState(false)
  const [mapType, setMapType] = useState<"satellite" | "street">("satellite")
  const [isClient, setIsClient] = useState(false)
  const mapRef = useRef<any>(null)

  useEffect(() => {
    setIsClient(true)
    // Import Leaflet CSS
    import("leaflet/dist/leaflet.css")
  }, [])

  useEffect(() => {
    setFields(buildInitialFields(t))
    setSelectedField(null)
    setEditingFieldData(false)
  }, [language])

  const handleMapClick = useCallback(
    (lat: number, lng: number) => {
      if (drawMode === "draw") {
        setCurrentPoints((prev) => [...prev, [lat, lng]])
      }
    },
    [drawMode]
  )

  const handleFieldClick = useCallback(
    (field: FieldData) => {
      if (drawMode === "select") {
        setSelectedField(field)
        setEditingFieldData(false)
      }
    },
    [drawMode]
  )

  const finishDrawing = useCallback(() => {
    if (currentPoints.length >= 3) {
      const colorIndex = fields.length % FIELD_COLORS.length
      const newField: FieldData = {
        id: `field-${Date.now()}`,
        name: t.farmMap.newFieldNamePattern.replace("{n}", String(fields.length + 1)),
        coordinates: currentPoints,
        color: FIELD_COLORS[colorIndex].stroke,
        fillColor: FIELD_COLORS[colorIndex].fill,
        cropType: "corn",
        soilMoisture: 50,
        soilPH: 7.0,
        nitrogen: 40,
        area: Math.round(Math.random() * 50 + 20),
        lastUpdated: t.farmMap.justNow,
      }
      setFields((prev) => [...prev, newField])
      setSelectedField(newField)
      setEditingFieldData(true)
    }
    setCurrentPoints([])
    setDrawMode("select")
  }, [currentPoints, fields.length, t])

  const cancelDrawing = useCallback(() => {
    setCurrentPoints([])
    setDrawMode("select")
  }, [])

  const undoLastPoint = useCallback(() => {
    setCurrentPoints((prev) => prev.slice(0, -1))
  }, [])

  const deleteField = useCallback((fieldId: string) => {
    setFields((prev) => prev.filter((f) => f.id !== fieldId))
    setSelectedField(null)
  }, [])

  const updateFieldData = useCallback(
    (fieldId: string, key: keyof FieldData, value: any) => {
      const stamp = t.farmMap.justNow
      setFields((prev) =>
        prev.map((f) => (f.id === fieldId ? { ...f, [key]: value, lastUpdated: stamp } : f))
      )
      if (selectedField?.id === fieldId) {
        setSelectedField((prev) => (prev ? { ...prev, [key]: value, lastUpdated: stamp } : null))
      }
    },
    [selectedField, t]
  )

  const handleZoomIn = () => {
    if (mapRef.current) {
      mapRef.current.setZoom(mapRef.current.getZoom() + 1)
    }
  }

  const handleZoomOut = () => {
    if (mapRef.current) {
      mapRef.current.setZoom(mapRef.current.getZoom() - 1)
    }
  }

  const handleRecenter = () => {
    if (mapRef.current) {
      mapRef.current.setView(FARM_CENTER, 14)
    }
  }

  // Tile layer URLs
  const satelliteTileUrl =
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
  const streetTileUrl = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

  return (
    <section id="map" className="py-12 sm:py-16 md:py-20 bg-secondary/30">
      <div className="container mx-auto px-3 sm:px-4">
        <div className="text-center mb-8 sm:mb-12">
          <Badge variant="outline" className="mb-3 sm:mb-4 border-primary/30 text-primary text-xs sm:text-sm">
            {t.farmMap.badge}
          </Badge>
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-foreground mb-3 sm:mb-4 text-balance">
            {t.farmMap.title}
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto text-pretty px-2">
            {t.farmMap.description}
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Map Container */}
          <Card className="lg:col-span-2 overflow-hidden">
            <CardHeader className="pb-2 px-3 sm:px-6">
              <div className="flex flex-col gap-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                      <Layers className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
                      {t.farmMap.mapCardTitle}
                    </CardTitle>
                    <CardDescription className="text-xs sm:text-sm mt-1 hidden sm:block">
                      {t.farmMap.mapCardHint}
                    </CardDescription>
                  </div>
                  {/* Map Type Toggle - Compact on mobile */}
                  <div className="flex items-center border rounded-lg overflow-hidden flex-shrink-0">
                    <Button
                      variant={mapType === "satellite" ? "default" : "ghost"}
                      size="sm"
                      className="rounded-none h-8 px-2 sm:px-3"
                      onClick={() => setMapType("satellite")}
                    >
                      <Satellite className="h-4 w-4 sm:mr-1" />
                      <span className="hidden sm:inline">{t.farmMap.satellite}</span>
                    </Button>
                    <Button
                      variant={mapType === "street" ? "default" : "ghost"}
                      size="sm"
                      className="rounded-none h-8 px-2 sm:px-3"
                      onClick={() => setMapType("street")}
                    >
                      <Map className="h-4 w-4 sm:mr-1" />
                      <span className="hidden sm:inline">{t.farmMap.map}</span>
                    </Button>
                  </div>
                </div>
                
                {/* Draw Mode Toggle - Full width on mobile */}
                <div className="flex items-center gap-2">
                  <Button
                    variant={drawMode === "select" ? "default" : "outline"}
                    size="sm"
                    className="flex-1 sm:flex-none h-9 sm:h-8"
                    onClick={() => {
                      setDrawMode("select")
                      cancelDrawing()
                    }}
                  >
                    <MousePointer2 className="h-4 w-4 mr-1.5" />
                    {t.farmMap.select}
                  </Button>
                  <Button
                    variant={drawMode === "draw" ? "default" : "outline"}
                    size="sm"
                    className="flex-1 sm:flex-none h-9 sm:h-8"
                    onClick={() => setDrawMode("draw")}
                  >
                    <Pencil className="h-4 w-4 mr-1.5" />
                    {t.farmMap.drawField}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {/* Drawing Instructions */}
              {drawMode === "draw" && (
                <div className="bg-primary/10 border-b border-primary/20 px-3 sm:px-4 py-2 sm:py-3">
                  <p className="text-xs sm:text-sm text-primary font-medium mb-2 sm:mb-0 sm:inline">
                    {currentPoints.length === 0
                      ? t.farmMap.tapToDraw
                      : currentPoints.length === 1
                        ? t.farmMap.onePointPlaced
                        : t.farmMap.pointsPlacedCount.replace("{n}", String(currentPoints.length))}
                  </p>
                  <div className="flex items-center gap-1.5 sm:gap-2 sm:inline-flex sm:ml-4">
                    {currentPoints.length > 0 && (
                      <Button variant="ghost" size="sm" className="h-8 px-2 sm:px-3" onClick={undoLastPoint}>
                        <Undo2 className="h-4 w-4 sm:mr-1" />
                        <span className="hidden sm:inline">{t.farmMap.undo}</span>
                      </Button>
                    )}
                    {currentPoints.length >= 3 && (
                      <Button size="sm" className="h-8 px-2 sm:px-3" onClick={finishDrawing}>
                        <Check className="h-4 w-4 sm:mr-1" />
                        <span className="hidden sm:inline">{t.farmMap.finish}</span>
                        <span className="sm:hidden">{t.farmMap.done}</span>
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" className="h-8 px-2 sm:px-3" onClick={cancelDrawing}>
                      <X className="h-4 w-4 sm:mr-1" />
                      <span className="hidden sm:inline">{t.farmMap.cancel}</span>
                    </Button>
                  </div>
                </div>
              )}

              {/* Leaflet Map */}
              <div className="relative w-full aspect-square sm:aspect-[4/3] md:aspect-[16/10]">
                {isClient ? (
                  <>
                    <link
                      rel="stylesheet"
                      href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
                      crossOrigin=""
                    />
                    <MapContainer
                      center={FARM_CENTER}
                      zoom={14}
                      className="w-full h-full z-0"
                      ref={mapRef}
                      zoomControl={false}
                      style={{ cursor: drawMode === "draw" ? "crosshair" : "grab" }}
                    >
                      <TileLayer
                        attribution={
                          mapType === "satellite"
                            ? "&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
                            : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        }
                        url={mapType === "satellite" ? satelliteTileUrl : streetTileUrl}
                      />

                      {/* Map Click Handler */}
                      <MapClickHandler onMapClick={handleMapClick} drawMode={drawMode} />

                      {/* Existing Field Polygons */}
                      {fields.map((field) => (
                        <Polygon
                          key={field.id}
                          positions={field.coordinates}
                          pathOptions={{
                            color: selectedField?.id === field.id ? "#facc15" : field.color,
                            fillColor: field.fillColor,
                            fillOpacity: 0.5,
                            weight: selectedField?.id === field.id ? 4 : 2,
                          }}
                          eventHandlers={{
                            click: () => handleFieldClick(field),
                          }}
                        >
                          <Popup>
                            <div className="font-sans">
                              <p className="font-semibold text-sm">{field.name}</p>
                              <p className="text-xs text-gray-600">
                                {t.farmMap[field.cropType]} — {field.area} {t.farmMap.acres}
                              </p>
                            </div>
                          </Popup>
                        </Polygon>
                      ))}

                      {/* Current Drawing Polygon */}
                      {currentPoints.length >= 2 && (
                        <Polygon
                          positions={currentPoints}
                          pathOptions={{
                            color: "#16a34a",
                            fillColor: "rgba(22, 163, 74, 0.3)",
                            fillOpacity: 0.4,
                            weight: 3,
                            dashArray: "8, 4",
                          }}
                        />
                      )}
                    </MapContainer>

                    {/* Map Controls */}
                    <div className="absolute top-2 right-2 sm:top-4 sm:right-4 z-[1000] flex flex-col gap-1.5 sm:gap-2">
                      <Button
                        size="icon"
                        variant="secondary"
                        className="h-8 w-8 sm:h-9 sm:w-9 shadow-lg bg-card hover:bg-muted"
                        onClick={handleZoomIn}
                      >
                        <ZoomIn className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="secondary"
                        className="h-8 w-8 sm:h-9 sm:w-9 shadow-lg bg-card hover:bg-muted"
                        onClick={handleZoomOut}
                      >
                        <ZoomOut className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="secondary"
                        className="h-8 w-8 sm:h-9 sm:w-9 shadow-lg bg-card hover:bg-muted"
                        onClick={handleRecenter}
                      >
                        <LocateFixed className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* Location Badge */}
                    <div className="absolute bottom-2 left-2 sm:bottom-4 sm:left-4 z-[1000] bg-card/95 backdrop-blur-sm rounded-lg px-2 py-1.5 sm:px-3 sm:py-2 shadow-lg">
                      <div className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm">
                        <MapPin className="h-3 w-3 sm:h-4 sm:w-4 text-primary" />
                        <span className="font-medium">{t.farmMap.sampleFarm}</span>
                      </div>
                      <p className="text-[10px] sm:text-xs text-muted-foreground mt-0.5">
                        {fields.length} {t.farmMap.fieldsMapped}
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="w-full h-full bg-muted flex items-center justify-center">
                    <div className="text-center">
                      <Layers className="h-12 w-12 text-muted-foreground mx-auto mb-3 animate-pulse" />
                      <p className="text-muted-foreground">{t.farmMap.loadingMap}</p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Field Details Panel */}
          <Card className="h-fit order-first lg:order-last">
            <CardHeader className="px-4 sm:px-6 py-4">
              <CardTitle className="text-base sm:text-lg">{t.farmMap.fieldDetails}</CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                {selectedField ? t.farmMap.viewAndEdit : t.farmMap.selectOrDraw}
              </CardDescription>
            </CardHeader>
            <CardContent className="px-4 sm:px-6">
              {selectedField ? (
                <div className="space-y-4 sm:space-y-5">
                  {/* Field Name */}
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">{t.farmMap.fieldName}</label>
                    {editingFieldData ? (
                      <Input
                        value={selectedField.name}
                        onChange={(e) => updateFieldData(selectedField.id, "name", e.target.value)}
                        className="mt-1.5"
                      />
                    ) : (
                      <div className="flex items-center gap-2 mt-1">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: selectedField.color }}
                        />
                        <p className="text-foreground font-semibold">{selectedField.name}</p>
                      </div>
                    )}
                  </div>

                  {/* Area */}
                  <div className="flex items-center justify-between py-2 px-3 bg-muted/50 rounded-lg">
                    <span className="text-sm text-muted-foreground">{t.farmMap.totalArea}</span>
                    <span className="font-semibold">
                      {selectedField.area} {t.farmMap.acres}
                    </span>
                  </div>

                  {/* Crop Type */}
                  <div>
                    <label className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
                      <Leaf className="h-3.5 w-3.5" />
                      {t.farmMap.cropType}
                    </label>
                    {editingFieldData ? (
                      <select
                        value={selectedField.cropType}
                        onChange={(e) =>
                          updateFieldData(selectedField.id, "cropType", e.target.value as CropKey)
                        }
                        className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        {CROP_KEYS.map((crop) => (
                          <option key={crop} value={crop}>
                            {t.farmMap[crop]}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <p className="text-foreground font-medium mt-1">{t.farmMap[selectedField.cropType]}</p>
                    )}
                  </div>

                  {/* Soil Moisture */}
                  <div>
                    <label className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
                      <Droplets className="h-3.5 w-3.5" />
                      {t.farmMap.soilMoisture}
                    </label>
                    {editingFieldData ? (
                      <div className="mt-1.5 flex items-center gap-2">
                        <Input
                          type="number"
                          min="0"
                          max="100"
                          value={selectedField.soilMoisture}
                          onChange={(e) =>
                            updateFieldData(selectedField.id, "soilMoisture", parseInt(e.target.value) || 0)
                          }
                          className="flex-1"
                        />
                        <span className="text-sm text-muted-foreground">%</span>
                      </div>
                    ) : (
                      <div className="mt-1.5">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-medium">{selectedField.soilMoisture}%</span>
                          <span className="text-xs text-muted-foreground">
                            {selectedField.soilMoisture < 40
                              ? t.farmMap.moistureLow
                              : selectedField.soilMoisture < 70
                                ? t.farmMap.moistureOptimal
                                : t.farmMap.moistureHigh}
                          </span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${selectedField.soilMoisture}%`,
                              backgroundColor:
                                selectedField.soilMoisture < 40
                                  ? "#f59e0b"
                                  : selectedField.soilMoisture < 70
                                    ? "#22c55e"
                                    : "#3b82f6",
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Soil pH */}
                  <div>
                    <label className="text-sm font-medium text-muted-foreground flex items-center gap-1.5">
                      <FlaskConical className="h-3.5 w-3.5" />
                      {t.farmMap.soilPH}
                    </label>
                    {editingFieldData ? (
                      <Input
                        type="number"
                        min="0"
                        max="14"
                        step="0.1"
                        value={selectedField.soilPH}
                        onChange={(e) =>
                          updateFieldData(selectedField.id, "soilPH", parseFloat(e.target.value) || 0)
                        }
                        className="mt-1.5"
                      />
                    ) : (
                      <div className="flex items-center gap-2 mt-1">
                        <span className="font-medium">{selectedField.soilPH}</span>
                        <Badge variant="outline" className="text-xs">
                          {selectedField.soilPH < 6
                            ? t.farmMap.phAcidic
                            : selectedField.soilPH > 7.5
                              ? t.farmMap.phAlkaline
                              : t.farmMap.phNeutral}
                        </Badge>
                      </div>
                    )}
                  </div>

                  {/* Nitrogen Level */}
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">{t.farmMap.nitrogen}</label>
                    {editingFieldData ? (
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={selectedField.nitrogen}
                        onChange={(e) =>
                          updateFieldData(selectedField.id, "nitrogen", parseInt(e.target.value) || 0)
                        }
                        className="mt-1.5"
                      />
                    ) : (
                      <div className="mt-1.5">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-medium">{selectedField.nitrogen} ppm</span>
                          <span className="text-xs text-muted-foreground">
                            {selectedField.nitrogen < 30
                              ? t.farmMap.nitrogenStatusLow
                              : selectedField.nitrogen < 60
                                ? t.farmMap.nitrogenStatusGood
                                : t.farmMap.nitrogenStatusHigh}
                          </span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary rounded-full transition-all"
                            style={{ width: `${selectedField.nitrogen}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Last Updated */}
                  <p className="text-xs text-muted-foreground pt-2 border-t">
                    {t.farmMap.lastUpdatedLabel} {selectedField.lastUpdated}
                  </p>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    {editingFieldData ? (
                      <Button className="flex-1" onClick={() => setEditingFieldData(false)}>
                        <Check className="h-4 w-4 mr-1" />
                        {t.farmMap.saveChanges}
                      </Button>
                    ) : (
                      <Button variant="outline" className="flex-1" onClick={() => setEditingFieldData(true)}>
                        <Pencil className="h-4 w-4 mr-1" />
                        {t.farmMap.editData}
                      </Button>
                    )}
                    <Button
                      variant="destructive"
                      size="icon"
                      onClick={() => deleteField(selectedField.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 sm:py-8">
                  <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-3 sm:mb-4">
                    <MousePointer2 className="h-6 w-6 sm:h-8 sm:w-8 text-muted-foreground" />
                  </div>
                  <p className="text-sm sm:text-base text-muted-foreground mb-4 px-2">{t.farmMap.tapField}</p>
                  <Button variant="outline" className="h-10" onClick={() => setDrawMode("draw")}>
                    <Pencil className="h-4 w-4 mr-2" />
                    {t.farmMap.drawNewField}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Fields Summary */}
        <div className="mt-6 sm:mt-8">
          <h3 className="text-sm font-semibold text-muted-foreground mb-3 px-1">
            {t.farmMap.yourFieldsWithCount.replace("{count}", String(fields.length))}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {fields.map((field) => (
              <Card
                key={field.id}
                className={`cursor-pointer transition-all hover:shadow-md active:scale-[0.98] ${
                  selectedField?.id === field.id ? "ring-2 ring-primary bg-primary/5" : ""
                }`}
                onClick={() => {
                  setSelectedField(field)
                  setEditingFieldData(false)
                }}
              >
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 sm:w-4 sm:h-4 rounded-full flex-shrink-0"
                      style={{ backgroundColor: field.color }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate text-sm sm:text-base">{field.name}</p>
                      <p className="text-xs sm:text-sm text-muted-foreground">
                        {t.farmMap[field.cropType]} · {field.area} {t.farmMap.acres}
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="flex items-center gap-1 text-xs sm:text-sm">
                        <Droplets className="h-3 w-3 sm:h-3.5 sm:w-3.5 text-blue-500" />
                        <span>{field.soilMoisture}%</span>
                      </div>
                      <p className="text-xs text-muted-foreground">pH {field.soilPH}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
