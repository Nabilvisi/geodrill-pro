import React from 'react';

export interface BrandMarkProps {
  size?: number | string;
  variant?: 'mark' | 'full' | 'compact';
  className?: string;
}

export const BrandMark: React.FC<BrandMarkProps> = ({ size = 32, variant = 'full', className = '' }) => {
  return (
    <div className={`flex items-center gap-2 select-none ${className}`} style={{ height: size }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        {/* Subsurface layered strata */}
        <path d="M4 36C12 34 20 38 32 35C40 33 44 35 44 35" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" strokeDasharray="3 3"/>
        <path d="M4 42C14 40 24 44 36 41C42 40 44 41 44 41" stroke="#64748B" strokeWidth="2.5" strokeLinecap="round"/>

        {/* Directional trajectory forming letter G */}
        <path
          d="M26 6C15 6 8 14 8 24C8 34 16 42 27 42C37 42 42 35 42 26H26V20H46C46.5 28 42 46 26 46C13 46 4 36 4 24C4 11 14 2 28 2C35 2 41 5 44 9L38 14C35 11 31 8 26 8"
          fill="url(#gd-gradient)"
        />

        {/* Well target rings */}
        <circle cx="28" cy="24" r="7" stroke="#F97316" strokeWidth="2.5"/>
        <circle cx="28" cy="24" r="3" fill="#F97316"/>

        <defs>
          <linearGradient id="gd-gradient" x1="4" y1="2" x2="44" y2="44" gradientUnits="userSpaceOnUse">
            <stop stopColor="#0B3D91"/>
            <stop offset="0.6" stopColor="#0EA5B7"/>
            <stop offset="1" stopColor="#0284C7"/>
          </linearGradient>
        </defs>
      </svg>

      {variant !== 'mark' && (
        <div className="flex flex-col leading-none">
          <div className="flex items-center gap-1">
            <span className="font-bold tracking-tight text-slate-900 text-lg font-sans">GeoDrill</span>
            <span className="font-semibold text-sky-600 text-xs px-1.5 py-0.5 rounded bg-sky-50 border border-sky-200">PRO</span>
          </div>
          {variant === 'full' && (
            <span className="text-[10px] tracking-wider uppercase text-slate-500 font-medium">Workstation v0.9</span>
          )}
        </div>
      )}
    </div>
  );
};
