interface SkeletonProps {
  width?: string;
  height?: string;
  className?: string;
}

export function Skeleton({
  width,
  height,
  className = "",
}: SkeletonProps) {
  return (
    <div
      className={`bg-gray-200 rounded-[10px] animate-pulse ${className}`}
      style={{ width, height }}
    />
  );
}
