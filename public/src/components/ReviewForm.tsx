import { useState } from "react";
import { Star, Loader2, CheckCircle } from "lucide-react";
import { createReview } from "../api/client-cabinet.ts";
import { ApiError } from "../api/client.ts";
import type { ReviewCreateResponse } from "../api/types.ts";

interface ReviewFormProps {
  bookingId: string;
  onSubmit: (review: ReviewCreateResponse) => void;
  onClose: () => void;
}

export default function ReviewForm({
  bookingId,
  onSubmit,
  onClose,
}: ReviewFormProps) {
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [text, setText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) return;

    setIsSubmitting(true);
    setError("");

    try {
      const review = await createReview({
        booking_id: bookingId,
        rating,
        text: text.trim() || undefined,
      });
      setSuccess(true);
      setTimeout(() => {
        onSubmit(review);
      }, 1200);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError("Не удалось отправить отзыв. Попробуйте позже.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="mt-3 rounded-xl bg-green-50 p-4 flex items-center gap-3">
        <CheckCircle className="w-5 h-5 text-green-600 shrink-0" />
        <p className="text-sm font-medium text-green-700">
          Спасибо за отзыв!
        </p>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-xl border border-gray-100 p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-text-primary">Ваша оценка</p>
        <button
          onClick={onClose}
          className="text-xs text-text-secondary hover:text-text-primary"
        >
          Закрыть
        </button>
      </div>

      {/* Star rating */}
      <div className="flex gap-1 mb-4">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => setRating(star)}
            onMouseEnter={() => setHoveredRating(star)}
            onMouseLeave={() => setHoveredRating(0)}
            className="p-0.5 transition-transform active:scale-90"
          >
            <Star
              size={32}
              className={
                star <= (hoveredRating || rating)
                  ? "text-yellow-400 fill-yellow-400"
                  : "text-gray-300"
              }
            />
          </button>
        ))}
      </div>

      {/* Text area */}
      <div className="mb-3">
        <textarea
          placeholder="Расскажите о визите (необязательно)"
          value={text}
          onChange={(e) => {
            if (e.target.value.length <= 500) {
              setText(e.target.value);
            }
          }}
          rows={3}
          className="w-full rounded-xl border border-border px-4 py-3 text-sm text-text-primary placeholder:text-gray-400 outline-none transition-colors focus:border-accent resize-none"
        />
        <p className="text-xs text-text-secondary text-right mt-1">
          {text.length}/500
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-3 rounded-xl bg-destructive/10 px-4 py-2">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={rating === 0 || isSubmitting}
        className="w-full bg-accent text-white rounded-xl py-3 font-semibold text-sm active:opacity-90 transition-opacity disabled:opacity-60 flex items-center justify-center gap-2"
      >
        {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
        Отправить отзыв
      </button>
    </div>
  );
}
