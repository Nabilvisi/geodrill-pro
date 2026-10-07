import React from 'react';

export interface BrandMarkProps {
  size?: number | string;
  variant?: 'mark' | 'full' | 'compact';
  className?: string;
}

export const BrandMark: React.FC<BrandMarkProps> = ({size=36,variant='full',className=''}) => {
  const numeric=typeof size==='number'?size:36;
  return <div className={`geodrill-brand ${className}`} style={{minHeight:size}}>
    <svg className="brand-logo-svg" width={size} height={size} viewBox="0 0 128 128" fill="none" role="img" aria-label="GeoDrill Pro">
      <defs>
        <linearGradient id="gd-brand-gradient" x1="16" y1="8" x2="106" y2="114" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0B3D91"/><stop offset=".58" stopColor="#0EA5B7"/><stop offset="1" stopColor="#0284C7"/>
        </linearGradient>
        <clipPath id="gd-brand-clip">
          <path d="M67 10c-31 0-53 23-53 53s23 55 54 55c27 0 47-18 47-46H68v-18h58c3 42-20 68-58 68C29 122 6 96 6 63S32 4 68 4c18 0 34 7 45 19L98 38C90 30 80 26 68 26c-20 0-35 15-35 37s15 38 36 38c15 0 25-7 29-17H67z"/>
        </clipPath>
      </defs>
      <path d="M67 10c-31 0-53 23-53 53s23 55 54 55c27 0 47-18 47-46H68v-18h58c3 42-20 68-58 68C29 122 6 96 6 63S32 4 68 4c18 0 34 7 45 19L98 38C90 30 80 26 68 26c-20 0-35 15-35 37s15 38 36 38c15 0 25-7 29-17H67z" fill="url(#gd-brand-gradient)"/>
      <g clipPath="url(#gd-brand-clip)" fill="none" strokeLinecap="round">
        <path d="M-8 76c31-13 54 8 82-4 24-10 40-2 63-10" stroke="#E2E8F0" strokeWidth="8"/>
        <path d="M-8 91c34-12 56 10 88-2 24-9 37-2 59-9" stroke="#64748B" strokeWidth="9"/>
        <path d="M-8 108c32-11 59 9 91-2 23-8 37-2 57-7" stroke="#374151" strokeWidth="10"/>
      </g>
      <path d="M64 19v22c0 11 3 18 12 25 9 7 15 13 15 25" stroke="#fff" strokeWidth="6" strokeLinecap="round"/>
      <path d="M57 19h14M60 13h8M61 13l3-8 3 8M60 19l4-7 4 7" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="91" cy="91" r="12" fill="#fff" stroke="#F97316" strokeWidth="5"/><circle cx="91" cy="91" r="4.5" fill="#F97316"/>
      <path d="M91 73v7M91 102v7M73 91h7M102 91h7" stroke="#F97316" strokeWidth="3" strokeLinecap="round"/>
    </svg>
    {variant!=='mark'&&<div className="brand-wordmark" style={{fontSize:Math.max(10,numeric*.46)}}>
      <div className="brand-name">GeoDrill <span className="brand-pro">Pro</span></div>
      {variant==='full'&&<span className="brand-subtitle">Drilling Engineering Workstation</span>}
    </div>}
  </div>;
};
