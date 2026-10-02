export interface CentreLocationFields {
  address?: string | null;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
}

/**
 * Safely formats a diagnostic centre's location fields into a clean human-readable string.
 *
 * Example:
 * formatCentreAddress({
 *   address: "21 Linking Road, Bandra West",
 *   city: "Mumbai",
 *   state: "Maharashtra"
 * }) => "21 Linking Road, Bandra West, Mumbai, Maharashtra"
 *
 * Filters empty or null/undefined values to prevent stray punctuation like "📍 ,".
 * Returns null if no location fields exist or are empty.
 */
export const formatCentreAddress = (
  centre?: CentreLocationFields | null,
  options?: { includePincode?: boolean }
): string | null => {
  if (!centre) return null;

  const parts = [centre.address, centre.city, centre.state]
    .map((field) => (field ? field.trim() : ''))
    .filter((field) => field.length > 0);

  if (parts.length === 0) {
    if (options?.includePincode && centre.pincode && centre.pincode.trim()) {
      return centre.pincode.trim();
    }
    return null;
  }

  let result = parts.join(', ');

  if (options?.includePincode && centre.pincode && centre.pincode.trim()) {
    result += ` - ${centre.pincode.trim()}`;
  }

  return result;
};
