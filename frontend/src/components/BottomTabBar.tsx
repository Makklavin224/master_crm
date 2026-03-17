import { NavLink } from "react-router-dom";
import { CalendarDays, BookOpen, Scissors, Users, Settings } from "lucide-react";
import { ROUTES } from "../lib/constants.ts";

interface Tab {
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  ariaLabel: string;
}

const tabs: Tab[] = [
  {
    path: ROUTES.MASTER_DASHBOARD,
    icon: CalendarDays,
    label: "Сегодня",
    ariaLabel: "Сегодня",
  },
  {
    path: ROUTES.MASTER_BOOKINGS,
    icon: BookOpen,
    label: "Записи",
    ariaLabel: "Записи",
  },
  {
    path: ROUTES.MASTER_SERVICES,
    icon: Scissors,
    label: "Услуги",
    ariaLabel: "Услуги",
  },
  {
    path: ROUTES.MASTER_CLIENTS,
    icon: Users,
    label: "Клиенты",
    ariaLabel: "Клиенты",
  },
  {
    path: ROUTES.MASTER_SETTINGS,
    icon: Settings,
    label: "Настройки",
    ariaLabel: "Настройки",
  },
];

export function BottomTabBar() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-border z-40">
      <div
        className="flex items-center justify-around h-[56px]"
        style={{ paddingBottom: "calc(16px + env(safe-area-inset-bottom, 0px))" }}
      >
        {tabs.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            end={tab.path === ROUTES.MASTER_DASHBOARD}
            className="flex-1"
          >
            {({ isActive }) => (
              <div className="flex flex-col items-center justify-center gap-0.5 py-1">
                <tab.icon
                  className={`w-6 h-6 ${isActive ? "text-accent" : "text-text-secondary"}`}
                  {...(!isActive ? { "aria-label": tab.ariaLabel } : {})}
                />
                {isActive && (
                  <span className="text-[12px] font-semibold text-accent leading-none">
                    {tab.label}
                  </span>
                )}
              </div>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
