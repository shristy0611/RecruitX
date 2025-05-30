
import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  colorClass?: string; // Retained for potential specific overrides, but default will align with new theme.
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, colorClass }) => {
  // Default to new theme's surface color if no specific colorClass is provided
  const baseBgClass = colorClass || 'bg-neutral-850'; 

  return (
    <div className={`${baseBgClass} p-6 rounded-xl shadow-lg-dark border border-neutral-800 subtle-hover-lift flex flex-col justify-between min-h-[130px]`}>
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium uppercase tracking-wider text-neutral-400">{title}</p>
        <div className="text-3xl text-accent-DEFAULT opacity-80"> {/* Using new accent color (teal) */}
          {icon}
        </div>
      </div>
      <p className="text-4xl font-bold mt-1 text-neutral-100 self-start">{value}</p>
    </div>
  );
};

export default StatCard;
