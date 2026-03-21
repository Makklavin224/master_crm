import { Layout, Menu, Button, Switch, Breadcrumb, Space, Typography } from "antd";
import {
  CalendarOutlined,
  TeamOutlined,
  AppstoreOutlined,
  DollarOutlined,
  BarChartOutlined,
  StarOutlined,
  SettingOutlined,
  LogoutOutlined,
  SunOutlined,
  MoonOutlined,
} from "@ant-design/icons";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { useAuth } from "../stores/auth";
import { useThemeStore } from "../stores/theme";

const { Sider, Content, Header } = Layout;

const PAGE_TITLES: Record<string, string> = {
  "/calendar": "Календарь",
  "/clients": "Клиенты",
  "/services": "Услуги",
  "/payments": "Платежи",
  "/analytics": "Аналитика",
  "/reviews": "Отзывы",
  "/settings": "Настройки",
};

const menuItems = [
  { key: "/calendar", icon: <CalendarOutlined />, label: "Календарь" },
  { key: "/clients", icon: <TeamOutlined />, label: "Клиенты" },
  { key: "/services", icon: <AppstoreOutlined />, label: "Услуги" },
  { key: "/payments", icon: <DollarOutlined />, label: "Платежи" },
  { key: "/analytics", icon: <BarChartOutlined />, label: "Аналитика" },
  { key: "/reviews", icon: <StarOutlined />, label: "Отзывы" },
  { key: "/settings", icon: <SettingOutlined />, label: "Настройки" },
];

export function AdminLayout() {
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem("admin_sidebar_collapsed") === "true";
    } catch {
      return false;
    }
  });
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuth((s) => s.logout);
  const profile = useAuth((s) => s.profile);
  const { isDark, toggle } = useThemeStore();

  const basePath = location.pathname.startsWith("/clients/")
    ? "/clients"
    : location.pathname;
  const currentPageTitle = PAGE_TITLES[basePath] || "MasterCRM";

  useEffect(() => {
    document.title = `${currentPageTitle} — MasterCRM`;
  }, [currentPageTitle]);

  const handleCollapse = (val: boolean) => {
    setCollapsed(val);
    try {
      localStorage.setItem("admin_sidebar_collapsed", String(val));
    } catch {
      // Ignore storage errors
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={handleCollapse}
        breakpoint="lg"
        theme={isDark ? "dark" : "light"}
      >
        <div
          style={{
            padding: 16,
            textAlign: "center",
            fontWeight: 700,
            fontSize: collapsed ? 20 : 16,
            color: isDark ? "#fff" : "#6C5CE7",
          }}
        >
          {collapsed ? "M" : "MasterCRM"}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          theme={isDark ? "dark" : "light"}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: "0 24px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            background: isDark ? "#141414" : "#fff",
          }}
        >
          <Space>
            <Breadcrumb
              items={[
                { title: "MasterCRM" },
                { title: currentPageTitle },
              ]}
            />
          </Space>
          <Space>
            <Typography.Text type="secondary">
              {profile?.business_name || profile?.name || ""}
            </Typography.Text>
            <Switch
              checked={isDark}
              onChange={toggle}
              checkedChildren={<MoonOutlined />}
              unCheckedChildren={<SunOutlined />}
              aria-label={
                isDark
                  ? "Переключить на светлую тему"
                  : "Переключить на тёмную тему"
              }
            />
            <Button type="text" icon={<LogoutOutlined />} onClick={logout} />
          </Space>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
