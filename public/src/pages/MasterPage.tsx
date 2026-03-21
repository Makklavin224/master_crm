import { useParams, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import {
  useMasterProfile,
  useMasterServices,
  useMasterReviews,
} from "../api/master.ts";
import { ApiError } from "../api/client.ts";
import HeroSection from "../components/HeroSection.tsx";
import ServicesSection from "../components/ServicesSection.tsx";
import SlotsSection from "../components/SlotsSection.tsx";
import ReviewsSection from "../components/ReviewsSection.tsx";
import ContactsSection from "../components/ContactsSection.tsx";
import StickyBookButton from "../components/StickyBookButton.tsx";

export default function MasterPage() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();

  const profileQuery = useMasterProfile(username ?? "");
  const servicesQuery = useMasterServices(username ?? "");
  const reviewsQuery = useMasterReviews(username ?? "");

  const handleBook = (serviceId?: string) => {
    const params = serviceId ? `?service=${serviceId}` : "";
    navigate(`/${username}/book${params}`);
  };

  const handleSlotClick = (date: string, time: string) => {
    navigate(`/${username}/book?date=${date}&time=${time}`);
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

  return (
    <div className="pb-24">
      <HeroSection profile={profile} onBook={() => handleBook()} />

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
