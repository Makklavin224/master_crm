import { Star } from "lucide-react";

function pluralReviews(count: number): string {
  const abs = Math.abs(count);
  const lastTwo = abs % 100;
  const lastOne = abs % 10;
  if (lastTwo >= 11 && lastTwo <= 19) return `${count} отзывов`;
  if (lastOne === 1) return `${count} отзыв`;
  if (lastOne >= 2 && lastOne <= 4) return `${count} отзыва`;
  return `${count} отзывов`;
}

interface StarRatingProps {
  rating: number;
  count?: number;
  size?: "sm" | "md";
}

export default function StarRating({
  rating,
  count,
  size = "md",
}: StarRatingProps) {
  const starSize = size === "sm" ? 14 : 18;
  const textClass = size === "sm" ? "text-xs" : "text-sm";

  const stars = [];
  for (let i = 1; i <= 5; i++) {
    if (i <= Math.floor(rating)) {
      // Filled star
      stars.push(
        <Star
          key={i}
          size={starSize}
          className="text-yellow-400 fill-yellow-400"
        />,
      );
    } else if (i - rating < 1 && i - rating > 0) {
      // Half star - render as filled since half-fill is complex with lucide
      stars.push(
        <Star
          key={i}
          size={starSize}
          className="text-yellow-400 fill-yellow-400 opacity-60"
        />,
      );
    } else {
      // Empty star
      stars.push(
        <Star key={i} size={starSize} className="text-gray-300" />,
      );
    }
  }

  return (
    <div className="flex items-center gap-1">
      <div className="flex items-center gap-0.5">{stars}</div>
      <span className={`${textClass} font-medium text-text-primary ml-1`}>
        {rating.toFixed(1)}
      </span>
      {count !== undefined && (
        <span className={`${textClass} text-text-secondary`}>
          &middot; {pluralReviews(count)}
        </span>
      )}
    </div>
  );
}
