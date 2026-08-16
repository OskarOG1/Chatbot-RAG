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
import { etykieta, NAZWY_STRON } from '@/lib/admin';

export const WYSOKOSC = 260;

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

export function osie(th: ThemeTokens) {
  return {
    tick: { fill: th.ink2, fontSize: 12, fontFamily: BODY },
    axisLine: false as const,
    tickLine: false as const,
  };
}

export function Ramka({ tytul, children }: { tytul: string; children: React.ReactNode }) {
  const th = useTheme();

  return (
    <section
      style={{
        background: th.surface,
        border: `1px solid ${th.line}`,
        borderRadius: 14,
        padding: '18px 18px 10px',
        boxShadow: th.shadow,
        minWidth: 0,
      }}
    >
      <h2 style={{ margin: '0 0 12px', fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
        {tytul}
      </h2>
      <div style={{ width: '100%', height: WYSOKOSC }}>{children}</div>
    </section>
  );
}

export function WykresDzienny({ dane }: { dane: PozycjaDzienna[] }) {
  const th = useTheme();
  const os = osie(th);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={dane}>
        <CartesianGrid stroke={th.lineSoft} vertical={false} />
        <XAxis dataKey="dzien" minTickGap={24} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <YAxis allowDecimals={false} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ stroke: th.line }} />
        <Legend wrapperStyle={{ fontFamily: BODY, fontSize: 12, color: th.ink2 }} />
        <Line type="monotone" dataKey="zapytan" name="Zapytania" stroke={th.accent} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="odmowy" name="Odmowy" stroke={th.ink3} strokeWidth={2} dot={false} />
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
  const os = osie(th);
  const dopasowane = dane.map((d) => ({
    nazwa: etykieta(mapa, String(d[pole])),
    ile: Number(d.ile),
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={dopasowane} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid stroke={th.lineSoft} horizontal={false} />
        <XAxis type="number" allowDecimals={false} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <YAxis
          type="category"
          dataKey="nazwa"
          width={168}
          tick={os.tick}
          axisLine={os.axisLine}
          tickLine={os.tickLine}
        />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ fill: th.lineSoft }} />
        <Bar dataKey="ile" name="Liczba" fill={th.accent} radius={[0, 6, 6, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function WykresStron({ dane }: { dane: { strona: string; ile: number }[] }) {
  const th = useTheme();
  const kolor = (strona: string) => {
    if (strona === 'kupujacy') return th.accent;
    if (strona === 'sprzedajacy') return th.accentInk;
    if (strona === 'nieznana') return th.line;
    return th.ink3;
  };
  const dopasowane = dane.map((d) => ({ ...d, nazwa: etykieta(NAZWY_STRON, d.strona) }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={dopasowane}
          dataKey="ile"
          nameKey="nazwa"
          innerRadius={55}
          outerRadius={88}
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
  const os = osie(th);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={dane}>
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
          name="Koszt (USD)"
          stroke={th.accent}
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function WykresLatencji({ dane }: { dane: Latencja['histogram'] }) {
  const th = useTheme();
  const os = osie(th);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={dane}>
        <CartesianGrid stroke={th.lineSoft} vertical={false} />
        <XAxis dataKey="zakres" tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <YAxis allowDecimals={false} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ fill: th.lineSoft }} />
        <Bar dataKey="ile" name="Zapytania" fill={th.accent} radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
