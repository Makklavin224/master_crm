export interface MasterProfile {
  id: string;
  name: string;
  username: string | null;
  specialization: string | null;
  city: string | null;
  avatar_path: string | null;
  instagram_url: string | null;
  avg_rating: number | null;
  review_count: number;
}

export interface ServiceRead {
  id: string;
  master_id: string;
  name: string;
  description: string | null;
  duration_minutes: number;
  price: number;
  category: string | null;
  is_active: boolean;
  sort_order: number;
  created_at: string;
}

export interface AvailableSlot {
  time: string; // "HH:MM:SS"
}

export interface AvailableSlotsResponse {
  date: string;
  slots: AvailableSlot[];
}

export interface ReviewRead {
  id: string;
  rating: number;
  text: string | null;
  client_name: string;
  master_reply: string | null;
  master_replied_at: string | null;
  created_at: string;
}

export interface BookingCreate {
  master_id: string;
  service_id: string;
  starts_at: string;
  client_name: string;
  client_phone: string;
  source_platform: string;
}

export interface BookingRead {
  id: string;
  master_id: string;
  client_id: string | null;
  service_id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  source_platform: string;
  notes: string | null;
  created_at: string;
  service_name: string;
  client_name: string;
  client_phone: string;
}
