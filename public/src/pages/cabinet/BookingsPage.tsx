import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LogOut, RefreshCw } from "lucide-react";
import { useAuth } from "../../stores/auth.ts";
import { getClientBookings, cancelBooking } from "../../api/client-cabinet.ts";
import BookingCard from "../../components/BookingCard.tsx";
import ReviewForm from "../../components/ReviewForm.tsx";

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-gray-100 shadow-sm p-4 animate-pulse">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-gray-200" />
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-24 mb-1.5" />
          <div className="h-3.5 bg-gray-200 rounded w-32" />
        </div>
        <div className="h-6 bg-gray-200 rounded-full w-20" />
      </div>
      <div className="h-4 bg-gray-200 rounded w-48 mb-3" />
      <div className="flex gap-2">
        <div className="flex-1 h-9 bg-gray-200 rounded-xl" />
        <div className="flex-1 h-9 bg-gray-200 rounded-xl" />
      </div>
    </div>
  );
}

export default function BookingsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, isLoading: authLoading, checkSession, logout } = useAuth();

  const [reviewingBookingId, setReviewingBookingId] = useState<string | null>(
    null,
  );
  const [cancellingBookingId, setCancellingBookingId] = useState<string | null>(
    null,
  );

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate("/my", { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  const {
    data: bookings,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["client-bookings"],
    queryFn: getClientBookings,
    enabled: isAuthenticated,
  });

  const handleCancel = async (bookingId: string) => {
    const confirmed = window.confirm(
      "Вы уверены, что хотите отменить запись?",
    );
    if (!confirmed) return;

    setCancellingBookingId(bookingId);
    try {
      await cancelBooking(bookingId);
      await queryClient.invalidateQueries({ queryKey: ["client-bookings"] });
    } catch {
      alert("Не удалось отменить запись. Попробуйте позже.");
    } finally {
      setCancellingBookingId(null);
    }
  };

  const handleReschedule = (_bookingId: string) => {
    alert("Функция переноса записи находится в разработке");
  };

  const handleReview = (bookingId: string) => {
    setReviewingBookingId(
      reviewingBookingId === bookingId ? null : bookingId,
    );
  };

  const handleReviewSubmitted = () => {
    setReviewingBookingId(null);
    queryClient.invalidateQueries({ queryKey: ["client-bookings"] });
  };

  const handleLogout = () => {
    logout();
    navigate("/my", { replace: true });
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-full">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-6 pb-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-text-primary">
            Мои записи
          </h1>
          <button
            onClick={handleLogout}
            className="p-2 text-text-secondary hover:text-text-primary transition-colors"
            title="Выйти"
          >
            <LogOut size={20} />
          </button>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex flex-col gap-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {/* Error state */}
        {isError && (
          <div className="text-center py-12">
            <p className="text-text-secondary mb-4">
              Не удалось загрузить записи
            </p>
            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-accent border border-accent/30 rounded-xl active:opacity-70"
            >
              <RefreshCw size={16} />
              Повторить
            </button>
          </div>
        )}

        {/* Bookings */}
        {bookings && (
          <div className="flex flex-col gap-8">
            {/* Upcoming */}
            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3 sticky top-0 bg-white py-1 z-10">
                Предстоящие
              </h2>
              {bookings.upcoming.length === 0 ? (
                <p className="text-sm text-text-secondary py-4">
                  Нет предстоящих записей
                </p>
              ) : (
                <div className="flex flex-col gap-3">
                  {bookings.upcoming.map((booking) => (
                    <BookingCard
                      key={booking.id}
                      booking={booking}
                      type="upcoming"
                      onCancel={handleCancel}
                      onReschedule={handleReschedule}
                      onReview={handleReview}
                      isCancelling={cancellingBookingId === booking.id}
                    />
                  ))}
                </div>
              )}
            </section>

            {/* Past */}
            <section>
              <h2 className="text-lg font-semibold text-text-primary mb-3 sticky top-0 bg-white py-1 z-10">
                Прошедшие
              </h2>
              {bookings.past.length === 0 ? (
                <p className="text-sm text-text-secondary py-4">
                  Пока нет завершённых визитов
                </p>
              ) : (
                <div className="flex flex-col gap-3">
                  {bookings.past.map((booking) => (
                    <div key={booking.id}>
                      <BookingCard
                        booking={booking}
                        type="past"
                        onCancel={handleCancel}
                        onReschedule={handleReschedule}
                        onReview={handleReview}
                      />
                      {reviewingBookingId === booking.id && (
                        <ReviewForm
                          bookingId={booking.id}
                          onSubmit={handleReviewSubmitted}
                          onClose={() => setReviewingBookingId(null)}
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
