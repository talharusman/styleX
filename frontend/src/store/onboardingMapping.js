/**
 * Maps the onboarding UI vocabulary to the values the backend accepts
 * (see backend/app/onboarding/schemas.py). Unknown values map to null so a bad
 * value is reported to the user instead of being silently rejected by the API.
 */

// UI body-type id -> backend BodyType
const BODY_TYPES = {
  lean: 'ectomorph',
  average: 'rectangle',
  athletic: 'athletic',
  bulky: 'mesomorph',
};

// UI style id -> backend StylePreference
const STYLES = {
  minimal: 'minimalist',
  classic: 'classic',
  streetwear: 'streetwear',
  bohemian: 'bohemian',
  athletic: 'sporty',
  preppy: 'classic',
  edgy: 'streetwear',
  'smart-casual': 'business_casual',
  vintage: 'vintage',
  glamorous: 'trendy',
};

// Face-analysis skin depth -> backend SkinTone
const SKIN_TONES = { fair: 'fair', light: 'light', medium: 'medium', tan: 'tan', deep: 'dark' };

export const toBackendBodyType = (id) => BODY_TYPES[id] ?? null;
export const toBackendStyle = (id) => STYLES[id] ?? null;
export const toBackendSkinTone = (depth) => SKIN_TONES[depth] ?? null;

/** Build the three step payloads from the onboarding store data. */
export function buildStepPayloads({ faceAnalysis, bodyType, height, stylePreferences, favoriteColors, avoidColors }) {
  const skinTone = toBackendSkinTone(faceAnalysis?.skinTone);
  const body = toBackendBodyType(bodyType);
  const styles = [...new Set((stylePreferences || []).map(toBackendStyle).filter(Boolean))];

  return {
    skin: skinTone && faceAnalysis?.undertone
      ? { skin_tone: skinTone, undertone: faceAnalysis.undertone, confirmed_by_user: true }
      : null,
    body: body ? { body_type: body, ...(height ? { height: Number(height) } : {}) } : null,
    style: styles.length
      ? {
          primary_style: styles[0],
          secondary_styles: styles.slice(1),
          favorite_colors: favoriteColors || [],
          avoid_colors: avoidColors || [],
        }
      : null,
  };
}
