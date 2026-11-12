 "use client";

import React, { useState } from "react";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Recycle,
  Scale,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  MapPin,
  RefreshCw,
  Trash2,
  Activity,
  Award,
} from "lucide-react";

const initialHourlyData = [
  { hora: "08:00", plastico: 12, carton: 8, vidrio: 5, metal: 3 },
  { hora: "10:00", plastico: 19, carton: 14, vidrio: 9, metal: 6 },
  { hora: "12:00", plastico: 28, carton: 21, vidrio: 14, metal: 9 },
  { hora: "14:00", plastico: 35, carton: 25, vidrio: 18, metal: 12 },
  { hora: "16:00", plastico: 42, carton: 31, vidrio: 22, metal: 15 },
  { hora: "18:00", plastico: 51, carton: 38, vidrio: 27, metal: 19 },
];

const initialMaterialDistribution = [
  { name: "Plástico PET", value: 45, color: "#10b981" },
  { name: "Cartón / Papel", value: 30, color: "#3b82f6" },
  { name: "Vidrio", value: 15, color: "#f59e0b" },
  { name: "Aluminio / Metal", value: 10, color: "#8b5cf6" },
];

const initialStations = [
  {
    id: "UNMSM-01",
    nombre: "Comedor Universitario Central",
    distrito: "Ciudad Universitaria • Zona Centro",
    llenado: 92,
    pesoKg: 48.9,
    estado: "Crítico",
    ultimaDeteccion: "Botella PET (98.9% IA)",
  },
  {
    id: "UNMSM-02",
    nombre: "Puerta 3 - Av. Universitaria",
    distrito: "Ciudad Universitaria • Acceso Principal",
    llenado: 84,
    pesoKg: 42.5,
    estado: "Alerta",
    ultimaDeteccion: "Lata Aluminio (97.4% IA)",
  },
  {
    id: "UNMSM-03",
    nombre: "Pabellón FIEE - Ing. Electrónica y Eléctrica",
    distrito: "Ciudad Universitaria • Zona Norte",
    llenado: 58,
    pesoKg: 28.4,
    estado: "Óptimo",
    ultimaDeteccion: "Botella PET (98.5% IA)",
  },
  {
    id: "UNMSM-04",
    nombre: "Biblioteca Central Pedro Zulen",
    distrito: "Ciudad Universitaria • Plaza Fray Tomás",
    llenado: 42,
    pesoKg: 19.4,
    estado: "Óptimo",
    ultimaDeteccion: "Papel / Cartón (98.1% IA)",
  },
];

// Residuos realistas permitidos por cada punto del campus
const stationMaterials: Record<
  string,
  { label: string; weight: number; points: number }[]
> = {
  "UNMSM-01": [
    { label: "Botella PET (99.1% IA)", weight: 0.4, points: 15 },
    { label: "Lata Aluminio (97.8% IA)", weight: 0.2, points: 20 },
  ],
  "UNMSM-02": [
    { label: "Botella PET (99.0% IA)", weight: 0.4, points: 15 },
    { label: "Lata Aluminio (97.4% IA)", weight: 0.2, points: 20 },
    { label: "Botella Vidrio (98.2% IA)", weight: 0.6, points: 12 },
  ],
  "UNMSM-03": [
    { label: "Botella PET (98.5% IA)", weight: 0.4, points: 15 },
    { label: "Caja Cartón (95.6% IA)", weight: 0.7, points: 10 },
  ],
  "UNMSM-04": [
    { label: "Papel Bond / Apuntes (98.7% IA)", weight: 0.5, points: 10 },
    { label: "Caja Cartón (96.4% IA)", weight: 0.8, points: 10 },
  ],
};

export default function EcoPuntoDashboard() {
  const [stations, setStations] = useState(initialStations);
  const [hourlyData, setHourlyData] = useState(initialHourlyData);
  const [totalWeight, setTotalWeight] = useState(139.2);
  const [totalItems, setTotalItems] = useState(412);
  const [ecoPoints, setEcoPoints] = useState(2840);
  const [isSimulating, setIsSimulating] = useState(false);

  const simulateDeposit = () => {
    setIsSimulating(true);
    const randomStationIdx = Math.floor(Math.random() * stations.length);
    const targetStation = stations[randomStationIdx];
    const allowedMaterials = stationMaterials[targetStation.id];
    const randomMat =
      allowedMaterials[Math.floor(Math.random() * allowedMaterials.length)];

    setStations((prev) =>
      prev.map((st, idx) => {
        if (idx !== randomStationIdx) return st;
        const newFill = Math.min(100, st.llenado + 4);
        const newWeight = Number((st.pesoKg + randomMat.weight).toFixed(1));
        const newStatus =
          newFill >= 90 ? "Crítico" : newFill >= 80 ? "Alerta" : "Óptimo";
        return {
          ...st,
          llenado: newFill,
          pesoKg: newWeight,
          estado: newStatus,
          ultimaDeteccion: randomMat.label,
        };
      })
    );

    setTotalWeight((prev) => Number((prev + randomMat.weight).toFixed(1)));
    setTotalItems((prev) => prev + 1);
    setEcoPoints((prev) => prev + randomMat.points);

    setHourlyData((prev) => {
      const updated = [...prev];
      const last = { ...updated[updated.length - 1] };
      if (randomMat.label.includes("Papel") || randomMat.label.includes("Cartón")) {
        last.carton += 1;
      } else {
        last.plastico += 1;
      }
      updated[updated.length - 1] = last;
      return updated;
    });

    setTimeout(() => setIsSimulating(false), 400);
  };

  const emptyContainer = (id: string) => {
    setStations((prev) =>
      prev.map((st) =>
        st.id === id
          ? { ...st, llenado: 0, pesoKg: 0, estado: "Óptimo" }
          : st
      )
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 font-sans">
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6 mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
            <Recycle className="w-8 h-8 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
                Ecopunto UNMSM
              </h1>
              <span className="px-2.5 py-0.5 text-xs font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Campus IoT En Vivo
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Red inteligente de reciclaje en Ciudad Universitaria • Telemetría y Visión Artificial
            </p>
          </div>
        </div>

        <button
          onClick={simulateDeposit}
          className="flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 active:scale-95 transition-all text-white font-medium rounded-xl shadow-lg shadow-emerald-950/50 cursor-pointer"
        >
          <RefreshCw
            className={`w-4 h-4 ${isSimulating ? "animate-spin" : ""}`}
          />
          Simular Depósito IoT
        </button>
      </header>

      <main className="max-w-7xl mx-auto space-y-8">
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
            <div className="flex items-center justify-between text-slate-400 mb-3">
              <span className="text-sm font-medium">Peso Total en Campus</span>
              <Scale className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-3xl font-bold text-white">{totalWeight} kg</div>
            <p className="text-xs text-emerald-400 mt-2 flex items-center gap-1">
              <Activity className="w-3.5 h-3.5" /> +12.4% respecto a ayer
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
            <div className="flex items-center justify-between text-slate-400 mb-3">
              <span className="text-sm font-medium">Envases Clasificados (IA)</span>
              <Cpu className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-3xl font-bold text-white">{totalItems} und.</div>
            <p className="text-xs text-blue-400 mt-2">
              Precisión promedio del modelo: 97.2%
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
            <div className="flex items-center justify-between text-slate-400 mb-3">
              <span className="text-sm font-medium">Módulos en Alerta</span>
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <div className="text-3xl font-bold text-white">
              {stations.filter((s) => s.llenado >= 80).length} / {stations.length}
            </div>
            <p className="text-xs text-amber-400 mt-2">
              Umbral de recolección: ≥ 80% capacidad
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
            <div className="flex items-center justify-between text-slate-400 mb-3">
              <span className="text-sm font-medium">EcoPuntos Sanmarquinos</span>
              <Award className="w-5 h-5 text-purple-400" />
            </div>
            <div className="text-3xl font-bold text-white">
              {ecoPoints.toLocaleString("en-US")} pts
            </div>
            <p className="text-xs text-purple-400 mt-2">
              Beneficios canjeables para estudiantes
            </p>
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 p-6 rounded-2xl">
            <h2 className="text-lg font-semibold text-white mb-1">
              Flujo de Recolección en Ciudad Universitaria (Hoy)
            </h2>
            <p className="text-xs text-slate-400 mb-6">
              Cantidad de unidades detectadas por sensores ópticos en tiempo real
            </p>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={hourlyData}>
                  <defs>
                    <linearGradient id="colorPlastico" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorCarton" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="hora" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "12px",
                      color: "#f8fafc",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="plastico"
                    name="Plástico PET"
                    stroke="#10b981"
                    fillOpacity={1}
                    fill="url(#colorPlastico)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="carton"
                    name="Cartón"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorCarton)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-2xl flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">
                Composición de Residuos
              </h2>
              <p className="text-xs text-slate-400 mb-4">
                Distribución porcentual clasificada por IA
              </p>
            </div>

            <div className="h-52 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={initialMaterialDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {initialMaterialDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "10px",
                      color: "#f8fafc",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-2 gap-2 mt-4">
              {initialMaterialDistribution.map((item) => (
                <div
                  key={item.name}
                  className="flex items-center gap-2 text-xs text-slate-300"
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="truncate">{item.name}</span>
                  <span className="font-semibold text-white ml-auto">
                    {item.value}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold text-white">
                Estado de Contenedores en Ciudad Universitaria (UNMSM)
              </h2>
              <p className="text-xs text-slate-400">
                Sensores ultrasónicos de nivel de llenado y celdas de carga por punto del campus
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-xs uppercase text-slate-400 bg-slate-950/40">
                  <th className="py-3.5 px-6">Punto de Acopio</th>
                  <th className="py-3.5 px-6">Nivel de Llenado</th>
                  <th className="py-3.5 px-6">Peso Actual</th>
                  <th className="py-3.5 px-6">Última Detección IA</th>
                  <th className="py-3.5 px-6">Estado</th>
                  <th className="py-3.5 px-6 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70 text-sm">
                {stations.map((station) => {
                  const barColor =
                    station.llenado >= 90
                      ? "bg-rose-500"
                      : station.llenado >= 80
                      ? "bg-amber-500"
                      : "bg-emerald-500";

                  return (
                    <tr
                      key={station.id}
                      className="hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="py-4 px-6">
                        <div className="font-medium text-white flex items-center gap-2">
                          <MapPin className="w-4 h-4 text-emerald-400 shrink-0" />
                          {station.nombre}
                        </div>
                        <div className="text-xs text-slate-400 ml-6">
                          {station.id} • {station.distrito}
                        </div>
                      </td>

                      <td className="py-4 px-6 w-48">
                        <div className="flex items-center justify-between text-xs mb-1.5">
                          <span className="font-medium text-slate-200">
                            {station.llenado}%
                          </span>
                          <span className="text-slate-400">Capacidad</span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                            style={{ width: `${station.llenado}%` }}
                          />
                        </div>
                      </td>

                      <td className="py-4 px-6 font-medium text-slate-200">
                        {station.pesoKg} kg
                      </td>

                      <td className="py-4 px-6">
                        <span className="px-2.5 py-1 text-xs rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
                          {station.ultimaDeteccion}
                        </span>
                      </td>

                      <td className="py-4 px-6">
                        {station.estado === "Crítico" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/15 text-rose-400 border border-rose-500/30">
                            <AlertTriangle className="w-3.5 h-3.5" /> Crítico
                          </span>
                        )}
                        {station.estado === "Alerta" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30">
                            <AlertTriangle className="w-3.5 h-3.5" /> Alerta
                          </span>
                        )}
                        {station.estado === "Óptimo" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Óptimo
                          </span>
                        )}
                      </td>

                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => emptyContainer(station.id)}
                          title="Registrar vaciado de contenedor"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          Vaciar
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}