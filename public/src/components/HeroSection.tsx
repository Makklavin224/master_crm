import { MapPin } from "lucide-react";
import type { MasterProfile } from "../api/types.ts";
import StarRating from "./StarRating.tsx";

interface HeroSectionProps {
  profile: MasterProfile;
  onBook: () => void;
}

export default function HeroSection({ profile, onBook }: HeroSectionProps) {
  const initials = profile.name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <section className="px-4 py-6 flex flex-col items-center text-center">
      {/* Avatar */}
      {profile.avatar_path ? (
        <img
          src={profile.avatar_path}
          alt={profile.name}
          className="w-24 h-24 rounded-full object-cover"
        />
      ) : (
        <div className="w-24 h-24 rounded-full bg-accent/10 flex items-center justify-center">
          <span className="text-2xl font-bold text-accent">{initials}</span>
        </div>
      )}

      {/* Name */}
      <h1 className="text-2xl font-bold text-text-primary mt-4">
        {profile.name}
      </h1>

      {/* Specialization */}
      {profile.specialization && (
        <p className="text-body text-text-secondary mt-1">
          {profile.specialization}
        </p>
      )}

      {/* City */}
      {profile.city && (
        <div className="flex items-center gap-1 mt-1 text-text-secondary">
          <MapPin size={14} />
          <span className="text-caption">{profile.city}</span>
        </div>
      )}

      {/* Rating */}
      {profile.review_count > 0 && profile.avg_rating !== null && (
        <div className="mt-3">
          <StarRating
            rating={profile.avg_rating}
            count={profile.review_count}
            size="md"
          />
        </div>
      )}

      {/* CTA */}
      <button
        onClick={onBook}
        className="w-full mt-5 bg-accent text-white rounded-xl py-3.5 font-semibold text-base active:opacity-90 transition-opacity"
      >
        Записаться
      </button>
    </section>
  );
}
