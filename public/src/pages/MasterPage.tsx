import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import {
  useMasterProfile,
  useMasterServices,
  useMasterReviews,
  useMasterPortfolio,
} from "../api/master.ts";
import { ApiError } from "../api/client.ts";
import type { MasterProfile } from "../api/types.ts";
import HeroSection from "../components/HeroSection.tsx";
import PortfolioSection from "../components/PortfolioSection.tsx";
import ServicesSection from "../components/ServicesSection.tsx";
import SlotsSection from "../components/SlotsSection.tsx";
import ReviewsSection from "../components/ReviewsSection.tsx";
import ContactsSection from "../components/ContactsSection.tsx";
import StickyBookButton from "../components/StickyBookButton.tsx";

function setMetaTag(name: string, content: string, attr: "name" | "property" = "name") {
  let el = document.querySelector(`meta[${attr}="${name}"]`) as HTMLMetaElement | null;
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, name);
    document.head.appendChild(el);
  }
  el.content = content;
}

function updateMetaTags(profile: MasterProfile) {
  const title = profile.specialization
    ? `${profile.name} — ${profile.specialization} | МоиОкошки`
    : `${profile.name} | МоиОкошки`;
  document.title = title;

  const parts = [profile.specialization, profile.city].filter(Boolean);
  const ratingText = profile.avg_rating
    ? `★ ${profile.avg_rating} (${profile.review_count} отзывов)`
    : "";
  const description = `${profile.name}${parts.length ? " — " + parts.join(", ") : ""}. ${ratingText} Запишитесь онлайн.`.trim();

  setMetaTag("description", description);
  setMetaTag("og:title", title, "property");
  setMetaTag("og:description", description, "property");
  setMetaTag("og:type", "profile", "property");
  setMetaTag("og:site_name", "МоиОкошки", "property");

  const url = `https://moiokoshki.ru/m/${profile.username || profile.id}`;
  setMetaTag("og:url", url, "property");

  if (profile.avatar_path) {
    const imageUrl = `https://moiokoshki.ru/api/v1/media/${profile.avatar_path}`;
    setMetaTag("og:image", imageUrl, "property");
  }
}

export default function MasterPage() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();

  const profileQuery = useMasterProfile(username ?? "");
  const servicesQuery = useMasterServices(username ?? "");
  const reviewsQuery = useMasterReviews(username ?? "");
  const portfolioQuery = useMasterPortfolio(username ?? "");

  useEffect(() => {
    if (profileQuery.data) {
      updateMetaTags(profileQuery.data);
    }
    return () => {
      document.title = "МоиОкошки — Запись онлайн";
    };
  }, [profileQuery.data]);

  const handleBook = (serviceId?: string) => {
    const params = serviceId ? `?service=${serviceId}` : "";
    navigate(`/m/${username}/book${params}`);
  };

  const handleSlotClick = (date: string, time: string) => {
    navigate(`/m/${username}/book?date=${date}&time=${time}`);
  };

  // Loading state
  if (profileQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-full">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    );
  }

  // 404 state
  if (profileQuery.error) {
    const is404 =
      profileQuery.error instanceof ApiError &&
      profileQuery.error.status === 404;
    return (
      <div className="flex flex-col items-center justify-center min-h-full p-8 text-center">
        <h1 className="text-2xl font-bold text-text-primary mb-2">
          {is404 ? "Мастер не найден" : "Ошибка"}
        </h1>
        <p className="text-text-secondary">
          {is404
            ? "Возможно, ссылка устарела или мастер удалил свою страницу"
            : "Не удалось загрузить страницу. Попробуйте позже."}
        </p>
      </div>
    );
  }

  const profile = profileQuery.data!;
  const services = servicesQuery.data ?? [];
  const reviews = reviewsQuery.data ?? [];
  const portfolio = portfolioQuery.data ?? [];

  return (
    <div className="pb-24">
      <HeroSection profile={profile} onBook={() => handleBook()} />

      {portfolio.length > 0 && (
        <>
          <div className="h-px bg-border mx-4" />
          <PortfolioSection photos={portfolio} />
        </>
      )}

      <div className="h-px bg-border mx-4" />

      <ServicesSection services={services} onBook={handleBook} />

      <div className="h-px bg-border mx-4" />

      <SlotsSection
        username={username ?? ""}
        services={services}
        onSlotClick={handleSlotClick}
      />

      <div className="h-px bg-border mx-4" />

      <ReviewsSection
        reviews={reviews}
        avgRating={profile.avg_rating}
        reviewCount={profile.review_count}
      />

      <div className="h-px bg-border mx-4" />

      <ContactsSection profile={profile} />

      <StickyBookButton onClick={() => handleBook()} />
    </div>
  );
}
