import dayjs from "dayjs";
import type { ReviewRead } from "../api/types.ts";
import StarRating from "./StarRating.tsx";

interface ReviewsSectionProps {
  reviews: ReviewRead[];
  avgRating: number | null;
  reviewCount: number;
}

export default function ReviewsSection({
  reviews,
  avgRating,
  reviewCount,
}: ReviewsSectionProps) {
  return (
    <section className="px-4 py-5">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-text-primary">Отзывы</h2>
        {avgRating !== null && reviewCount > 0 && (
          <StarRating rating={avgRating} count={reviewCount} size="sm" />
        )}
      </div>

      {reviews.length === 0 ? (
        <p className="text-body text-text-secondary">Пока нет отзывов</p>
      ) : (
        <div className="space-y-3">
          {reviews.slice(0, 10).map((review) => (
            <div key={review.id} className="rounded-xl bg-surface p-4">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-text-primary text-sm">
                  {review.client_name}
                </span>
                <span className="text-caption text-text-secondary">
                  {dayjs(review.created_at).format("DD.MM.YYYY")}
                </span>
              </div>

              <StarRating rating={review.rating} size="sm" />

              {review.text && (
                <p className="text-body text-text-primary mt-2">
                  {review.text}
                </p>
              )}

              {review.master_reply && (
                <div className="bg-white rounded-lg p-3 mt-2">
                  <p className="text-caption text-text-secondary italic">
                    Ответ мастера:
                  </p>
                  <p className="text-body text-text-primary mt-0.5 italic">
                    {review.master_reply}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
