import { useState, useEffect, useCallback } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import type { PortfolioPhoto } from "../api/types.ts";

interface PortfolioSectionProps {
  photos: PortfolioPhoto[];
}

export default function PortfolioSection({ photos }: PortfolioSectionProps) {
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const [touchStartX, setTouchStartX] = useState<number | null>(null);

  if (photos.length === 0) return null;

  const tags = [
    ...new Set(
      photos
        .map((p) => p.service_tag)
        .filter((t): t is string => t !== null),
    ),
  ];

  const filteredPhotos = selectedTag
    ? photos.filter((p) => p.service_tag === selectedTag)
    : photos;

  const openLightbox = (index: number) => setLightboxIndex(index);
  const closeLightbox = () => setLightboxIndex(null);

  const goPrev = useCallback(() => {
    setLightboxIndex((prev) =>
      prev !== null ? Math.max(0, prev - 1) : null,
    );
  }, []);

  const goNext = useCallback(() => {
    setLightboxIndex((prev) =>
      prev !== null
        ? Math.min(filteredPhotos.length - 1, prev + 1)
        : null,
    );
  }, [filteredPhotos.length]);

  /* Keyboard navigation */
  useEffect(() => {
    if (lightboxIndex === null) return;

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeLightbox();
      else if (e.key === "ArrowLeft") goPrev();
      else if (e.key === "ArrowRight") goNext();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [lightboxIndex, goPrev, goNext]);

  /* Prevent body scroll when lightbox open */
  useEffect(() => {
    if (lightboxIndex !== null) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = prev;
      };
    }
  }, [lightboxIndex]);

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStartX(e.touches[0].clientX);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX === null) return;
    const diff = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(diff) > 50) {
      if (diff > 0) goPrev();
      else goNext();
    }
    setTouchStartX(null);
  };

  const pillBase =
    "px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors";
  const pillInactive = `${pillBase} bg-surface text-text-secondary border border-border`;
  const pillActive = `${pillBase} bg-accent text-white`;

  return (
    <section className="px-4 py-6">
      <h2 className="text-lg font-semibold text-text-primary mb-4">
        Портфолио
      </h2>

      {/* Tag filter pills */}
      {tags.length > 0 && (
        <div className="flex gap-2 mb-4 overflow-x-auto scrollbar-hide">
          <button
            onClick={() => setSelectedTag(null)}
            className={selectedTag === null ? pillActive : pillInactive}
          >
            Все
          </button>
          {tags.map((tag) => (
            <button
              key={tag}
              onClick={() => setSelectedTag(tag)}
              className={selectedTag === tag ? pillActive : pillInactive}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      {/* Horizontal scroll gallery */}
      <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-2">
        {filteredPhotos.map((photo, index) => (
          <button
            key={photo.id}
            onClick={() => openLightbox(index)}
            className="flex-shrink-0 rounded-xl overflow-hidden"
          >
            <img
              src={`/api/v1/media/${photo.thumbnail_path}`}
              alt={photo.caption || "Работа мастера"}
              className="w-28 h-28 object-cover"
              loading="lazy"
            />
          </button>
        ))}
      </div>

      {/* Lightbox overlay */}
      {lightboxIndex !== null && filteredPhotos[lightboxIndex] && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeLightbox();
          }}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {/* Close button */}
          <button
            onClick={closeLightbox}
            className="absolute top-4 right-4 text-white p-2"
            aria-label="Закрыть"
          >
            <X size={28} />
          </button>

          {/* Prev arrow */}
          {lightboxIndex > 0 && (
            <button
              onClick={goPrev}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-white p-2"
              aria-label="Предыдущее фото"
            >
              <ChevronLeft size={32} />
            </button>
          )}

          {/* Image + caption */}
          <div className="flex flex-col items-center px-12">
            <img
              src={`/api/v1/media/${filteredPhotos[lightboxIndex].file_path}`}
              alt={filteredPhotos[lightboxIndex].caption || "Работа мастера"}
              className="max-w-full max-h-[85vh] object-contain"
            />
            {filteredPhotos[lightboxIndex].caption && (
              <p className="text-white text-center mt-2">
                {filteredPhotos[lightboxIndex].caption}
              </p>
            )}
          </div>

          {/* Next arrow */}
          {lightboxIndex < filteredPhotos.length - 1 && (
            <button
              onClick={goNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-white p-2"
              aria-label="Следующее фото"
            >
              <ChevronRight size={32} />
            </button>
          )}
        </div>
      )}
    </section>
  );
}
