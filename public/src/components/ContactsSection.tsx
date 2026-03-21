import { MapPin, Instagram } from "lucide-react";
import type { MasterProfile } from "../api/types.ts";

interface ContactsSectionProps {
  profile: MasterProfile;
}

export default function ContactsSection({ profile }: ContactsSectionProps) {
  const hasInstagram = !!profile.instagram_url;
  const hasCity = !!profile.city;

  if (!hasInstagram && !hasCity) return null;

  return (
    <section className="px-4 py-5">
      <h2 className="text-lg font-semibold text-text-primary mb-3">
        Контакты
      </h2>

      <div className="space-y-3">
        {hasInstagram && (
          <a
            href={profile.instagram_url!}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 text-accent hover:underline"
          >
            <Instagram size={20} />
            <span className="text-body">Instagram</span>
          </a>
        )}

        {hasCity && (
          <div className="flex items-center gap-3 text-text-secondary">
            <MapPin size={20} />
            <span className="text-body">{profile.city}</span>
          </div>
        )}
      </div>
    </section>
  );
}
