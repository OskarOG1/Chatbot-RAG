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

export function Ramka({ tytul, opis, children }: { tytul: string; opis?: string; children: React.ReactNode }) {
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
      <h2 style={{ margin: '0 0 4px', fontFamily: DISPLAY, fontSize: 15, fontWeight: 700, color: th.ink }}>
        {tytul}
      </h2>
      {opis ? (
        <p style={{ margin: '0 0 12px', fontFamily: BODY, fontSize: 12, color: th.ink3 }}>{opis}</p>
      ) : (
        <div style={{ height: 12 }} />
      )}
      <div style={{ width: '100%', height: WYSOKOSC }}>{children}</div>
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
  const os = osie(th);

  if (dane.length < 2) {
    return <BrakTrendu tekst="Za mało dni, żeby pokazać trend. Wróć po kolejnym dniu z ruchem." />;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={dane}>
        <CartesianGrid stroke={th.lineSoft} vertical={false} />
        <XAxis dataKey="dzien" minTickGap={24} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <YAxis allowDecimals={false} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ stroke: th.line }} />
        <Legend wrapperStyle={{ fontFamily: BODY, fontSize: 12, color: th.ink2 }} />
        <Line type="monotone" dataKey="zapytan" name="Pytania" stroke={PALETA[0]} strokeWidth={2.5} dot={false} />
        <Line
          type="monotone"
          dataKey="odmowy"
          name="Bez odpowiedzi"
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
          width={220}
          tick={os.tick}
          axisLine={os.axisLine}
          tickLine={os.tickLine}
        />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ fill: th.lineSoft }} />
        <Bar dataKey="ile" name="Liczba" radius={[0, 6, 6, 0]} barSize={18}>
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
  const kolor = (strona: string) => {
    if (strona === 'kupujacy') return KOLOR_KUPUJACY;
    if (strona === 'sprzedajacy') return KOLOR_SPRZEDAJACY;
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
  const os = osie(th);

  if (dane.length < 2) {
    return <BrakTrendu tekst="Za mało dni, żeby pokazać koszt w czasie." />;
  }

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
          name="Koszt dzienny (USD)"
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
  const os = osie(th);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={dane}>
        <CartesianGrid stroke={th.lineSoft} vertical={false} />
        <XAxis dataKey="zakres" tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <YAxis allowDecimals={false} tick={os.tick} axisLine={os.axisLine} tickLine={os.tickLine} />
        <Tooltip contentStyle={stylTooltipa(th)} cursor={{ fill: th.lineSoft }} />
        <Bar dataKey="ile" name="Pytania" radius={[6, 6, 0, 0]}>
          {dane.map((d, i) => (
            <Cell key={d.zakres} fill={KOLORY_LATENCJI[i % KOLORY_LATENCJI.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
