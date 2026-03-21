import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../stores/auth.ts";
import LoginForm from "../../components/LoginForm.tsx";

export default function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, checkSession } = useAuth();

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate("/my/bookings", { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-full">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-full px-4 py-8">
      <div className="w-full max-w-sm text-center mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2">
          Личный кабинет
        </h1>
        <p className="text-text-secondary">
          Войдите, чтобы видеть свои записи
        </p>
      </div>
      <LoginForm />
    </div>
  );
}
