'use client';

import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import { useTheme, BODY, DISPLAY, type ThemeTokens } from '@/lib/theme';
import type { PozycjaDzienna, Latencja } from '@/lib/admin';
import { etykieta } from '@/lib/admin';
import { useTekstyAdmina } from '@/lib/adminTeksty';
import { useWaskiEkran } from '@/lib/ekran';

export const WYSOKOSC = 260;

export const PALETA = [
  '#FF5A00',
  '#2D7FF9',
  '#12A594',
  '#8B5CF6',
  '#F5A524',
  '#E5484D',
  '#0EA5E9',
  '#84CC16',
];

export const KOLOR_ODMOWY = '#E5484D';
export const KOLOR_KUPUJACY = '#2D7FF9';
export const KOLOR_SPRZEDAJACY = '#FF5A00';

const KOLORY_LATENCJI = ['#12A594', '#84CC16', '#F5A524', '#F97316', '#E5484D'];
const WIERSZ_WASKI = 48;

export function wysokoscPoziomego(liczbaPozycji: number, waski: boolean): number {
  return waski ? Math.max(WYSOKOSC, liczbaPozycji * WIERSZ_WASKI + 36) : WYSOKOSC;
}

export function stylTooltipa(th: ThemeTokens) {
  return {
    background: th.surface,
    border: `1px solid ${th.line}`,
    borderRadius: 10,
    fontFamily: BODY,
    fontSize: 12.5,
    color: th.ink,
    boxShadow: th.shadow,
  };
}

export function osie(th: ThemeTokens, waski = false) {
  return {
    tick: { fill: th.ink2, fontSize: waski ? 11 : 12, fontFamily: BODY },
    axisLine: false as const,
    tickLine: false as const,
  };
}

export function Ramka({
  tytul,
  opis,
  wysokosc = WYSOKOSC,
  children,
}: {
  tytul: string;
  opis?: string;
  wysokosc?: number;
  children: React.ReactNode;
}) {
  const th = useTheme();
  const waski = useWaskiEkran();

  return (
    <section
      style={{
        background: th.surface,
        border: `1px solid ${th.line}`,
        borderRadius: 14,
        padding: waski ? '14px 12px 8px' : '18px 18px 10px',
        boxShadow: th.shadow,
        minWidth: 0,
      }}
    >
      <h2 style={{ margin: '0 0 4px', fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
        {tytul}
      </h2>
      {opis ? (
        <p style={{ margin: '0 0 12px', fontFamily: BODY, fontSize: 12, color: th.ink3 }}>{opis}</p>
      ) : (
        <div style={{ height: 12 }} />
      )}
      <div style={{ width: '100%', height: wysokosc }}>{children}</div>
    </section>
  );
}

export function BrakTrendu({ tekst }: { tekst: string }) {
  const th = useTheme();

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: 20,
        borderRadius: 12,
        border: `1px dashed ${th.line}`,
        background: th.raised,
        fontFamily: BODY,
        fontSize: 13,
        color: th.ink3,
      }}
    >
      {tekst}
    </div>
  );
}

export function WykresDzienny({ dane }: { dane: PozycjaDzienna[] }) {
  const th = useTheme();
  const t = useTekstyAdmina();
  const waski = useWaskiEkran();
  const os = osie(th, waski);

  if (dane.length < 2) {
    return <BrakTrendu tekst={t.zaMaloDniTrend} />;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={dane} margin={waski ? { top: 5, right: 8, bottom: 0, left: -12 } : undefined}>
        <CartesianGrid stroke={th.lineSoft} vertical={false} />
        <XAxis dataKey="dzien" minTickGap={24} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <YAxis allowDecimals={false} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ stroke: th.line }} />
        <Legend wrapperStyle={{ fontFamily: BODY, fontSize: 12, color: th.ink2 }} />
        <Line type="monotone" dataKey="zapytan" name={t.seriaPytania} stroke={PALETA[0]} strokeWidth={2.5} dot={false} />
        <Line
          type="monotone"
          dataKey="odmowy"
          name={t.seriaBezOdpowiedzi}
          stroke={KOLOR_ODMOWY}
          strokeWidth={2}
          strokeDasharray="5 4"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function WykresPoziomy({
  dane,
  mapa,
  pole,
}: {
  dane: Record<string, unknown>[];
  mapa: Record<string, string>;
  pole: string;
}) {
  const th = useTheme();
  const t = useTekstyAdmina();
  const waski = useWaskiEkran();
  const os = osie(th, waski);
  const szerokoscOsi = waski ? 116 : 220;
  const dopasowane = dane.map((d) => ({
    nazwa: etykieta(mapa, String(d[pole])),
    ile: Number(d.ile),
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={dopasowane} layout="vertical" margin={{ top: 4, right: waski ? 8 : 16, bottom: 0, left: waski ? 0 : 8 }}>
        <CartesianGrid stroke={th.lineSoft} horizontal={false} />
        <XAxis type="number" allowDecimals={false} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <YAxis
          type="category"
          dataKey="nazwa"
          width={szerokoscOsi}
          interval={0}
          tick={{ ...os.tick, width: szerokoscOsi - 8 }}
          axisLine={os.axisLine}
          tickLine={os.tickLine}
        />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ fill: th.lineSoft }} />
        <Bar dataKey="ile" name={t.seriaLiczba} radius={[0, 6, 6, 0]} barSize={waski ? 14 : 18}>
          {dopasowane.map((d, i) => (
            <Cell key={d.nazwa} fill={PALETA[i % PALETA.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function WykresStron({ dane }: { dane: { strona: string; ile: number }[] }) {
  const th = useTheme();
  const t = useTekstyAdmina();
  const waski = useWaskiEkran();
  const kolor = (strona: string) => {
    if (strona === 'kupujacy') return KOLOR_KUPUJACY;
    if (strona === 'sprzedajacy') return KOLOR_SPRZEDAJACY;
    return th.ink3;
  };
  const dopasowane = dane.map((d) => ({ ...d, nazwa: etykieta(t.nazwyStron, d.strona) }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={dopasowane}
          dataKey="ile"
          nameKey="nazwa"
          innerRadius={waski ? 48 : 55}
          outerRadius={waski ? 78 : 88}
          paddingAngle={2}
          stroke={th.surface}
          strokeWidth={2}
        >
          {dopasowane.map((d) => (
            <Cell key={d.strona} fill={kolor(d.strona)} />
          ))}
        </Pie>
        <Tooltip contentStyle={stylTooltipa(th)} />
        <Legend wrapperStyle={{ fontFamily: BODY, fontSize: 12, color: th.ink2 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function WykresKosztu({ dane }: { dane: PozycjaDzienna[] }) {
  const th = useTheme();
  const t = useTekstyAdmina();
  const waski = useWaskiEkran();
  const os = osie(th, waski);

  if (dane.length < 2) {
    return <BrakTrendu tekst={t.zaMaloDniKoszt} />;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={dane} margin={waski ? { top: 5, right: 8, bottom: 0, left: 0 } : undefined}>
        <CartesianGrid stroke={th.lineSoft} vertical={false} />
        <XAxis dataKey="dzien" minTickGap={24} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <YAxis
          allowDecimals
          tickFormatter={(wartosc: number) => wartosc.toFixed(4)}
          tick={os.tick}
          axisLine={os.axisLine}
          tickLine={os.tickLine}
        />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ stroke: th.line }} />
        <Legend wrapperStyle={{ fontFamily: BODY, fontSize: 12, color: th.ink2 }} />
        <Line
          type="monotone"
          dataKey="koszt_usd"
          name={t.seriaKoszt}
          stroke={PALETA[3]}
          strokeWidth={2.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function WykresLatencji({ dane }: { dane: Latencja['histogram'] }) {
  const th = useTheme();
  const t = useTekstyAdmina();
  const waski = useWaskiEkran();
  const os = osie(th, waski);
  const dopasowane = dane.map((d) => ({ ...d, zakres: etykieta(t.przedzialyLatencji, d.zakres) }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={dopasowane} margin={waski ? { top: 5, right: 4, bottom: 0, left: -18 } : undefined}>
        <CartesianGrid stroke={th.lineSoft} vertical={false} />
        <XAxis
          dataKey="zakres"
          interval={0}
          height={waski ? 40 : 30}
          tick={waski ? { ...os.tick, fontSize: 10, width: 36 } : os.tick}
          axisLine={os.axisLine}
          tickLine={os.tickLine}
        />
        <YAxis allowDecimals={false} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ fill: th.lineSoft }} />
        <Bar dataKey="ile" name={t.seriaPytania} radius={[6, 6, 0, 0]}>
          {dopasowane.map((d, i) => (
            <Cell key={d.zakres} fill={KOLORY_LATENCJI[i % KOLORY_LATENCJI.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
