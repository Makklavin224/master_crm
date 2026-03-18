import type { ThemeConfig } from "antd";
import { theme } from "antd";

export const lightTheme: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: "#6C5CE7",
    borderRadius: 8,
    fontFamily: "'Inter', -apple-system, sans-serif",
  },
};

export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: "#6C5CE7",
    borderRadius: 8,
    fontFamily: "'Inter', -apple-system, sans-serif",
  },
};
