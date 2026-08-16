'use client';

import dynamic from 'next/dynamic';

const PanelAdmina = dynamic(() => import('@/components/admin/PanelAdmina'), { ssr: false });

export default function Page() {
  return <PanelAdmina />;
}
