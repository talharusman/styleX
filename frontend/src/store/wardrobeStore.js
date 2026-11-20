import { create } from 'zustand';
import { wardrobeApi, parseApiError } from '../api';

/**
 * Wardrobe store: real data only. Every section tracks its own loading/error
 * state, and `errorCode` lets the UI show the right call-to-action
 * (e.g. profile_incomplete -> go finish the selfie analysis).
 */
const section = () => ({ data: null, loading: false, error: null, errorCode: null });

const errorState = (error) => {
  const { message, details } = parseApiError(error);
  return { loading: false, error: message, errorCode: details?.error_code ?? null };
};

const useWardrobeStore = create((set, get) => ({
  items: { ...section(), data: [] },
  recommendations: section(),
  outfits: section(),
  saved: { ...section(), data: [] },
  uploading: false,
  uploadError: null,

  fetchItems: async () => {
    set((s) => ({ items: { ...s.items, loading: true, error: null } }));
    try {
      const { data } = await wardrobeApi.listItems();
      set({ items: { data: data.items, loading: false, error: null, errorCode: null } });
    } catch (e) {
      set((s) => ({ items: { ...s.items, ...errorState(e) } }));
    }
  },

  fetchRecommendations: async (occasion) => {
    set({ recommendations: { ...section(), loading: true } });
    try {
      const { data } = await wardrobeApi.recommendations(occasion ? { occasion } : {});
      set({ recommendations: { data, loading: false, error: null, errorCode: null } });
    } catch (e) {
      set({ recommendations: { ...section(), ...errorState(e) } });
    }
  },

  fetchOutfits: async (occasion) => {
    set({ outfits: { ...section(), loading: true } });
    try {
      const { data } = await wardrobeApi.outfits(occasion ? { occasion } : {});
      set({ outfits: { data, loading: false, error: null, errorCode: null } });
    } catch (e) {
      set({ outfits: { ...section(), ...errorState(e) } });
    }
  },

  fetchSaved: async () => {
    set((s) => ({ saved: { ...s.saved, loading: true, error: null } }));
    try {
      const { data } = await wardrobeApi.savedOutfits();
      set({ saved: { data: data.outfits, loading: false, error: null, errorCode: null } });
    } catch (e) {
      set((s) => ({ saved: { ...s.saved, ...errorState(e) } }));
    }
  },

  /** Recommendations and outfits depend on the wardrobe: refresh them after any change. */
  refreshDerived: async () => {
    await Promise.all([get().fetchRecommendations(), get().fetchOutfits(), get().fetchSaved()]);
  },

  uploadItem: async (file) => {
    set({ uploading: true, uploadError: null });
    try {
      await wardrobeApi.addItem(file);
      await get().fetchItems();
      get().refreshDerived();
      set({ uploading: false });
      return { success: true };
    } catch (e) {
      const { message } = parseApiError(e);
      set({ uploading: false, uploadError: message });
      return { success: false, error: message };
    }
  },

  updateItem: async (id, changes) => {
    try {
      await wardrobeApi.updateItem(id, changes);
      await get().fetchItems();
      get().refreshDerived();
      return { success: true };
    } catch (e) {
      return { success: false, error: parseApiError(e).message };
    }
  },

  toggleFavorite: async (id) => {
    // optimistic, rolled back on failure
    const previous = get().items.data;
    set((s) => ({
      items: { ...s.items, data: s.items.data.map((i) => (i.id === id ? { ...i, is_favorite: !i.is_favorite } : i)) },
    }));
    try {
      await wardrobeApi.toggleFavorite(id);
    } catch {
      set((s) => ({ items: { ...s.items, data: previous } }));
    }
  },

  deleteItem: async (id) => {
    try {
      await wardrobeApi.deleteItem(id);
      await get().fetchItems();
      get().refreshDerived();
      return { success: true };
    } catch (e) {
      return { success: false, error: parseApiError(e).message };
    }
  },

  saveOutfit: async (outfit) => {
    try {
      await wardrobeApi.saveOutfit({
        name: 'My outfit',
        item_ids: outfit.items.map((r) => r.item.id),
        score: outfit.outfit_score,
        reasoning: outfit.reasoning,
      });
      await get().fetchSaved();
      return { success: true };
    } catch (e) {
      return { success: false, error: parseApiError(e).message };
    }
  },

  deleteSavedOutfit: async (id) => {
    try {
      await wardrobeApi.deleteSavedOutfit(id);
      await get().fetchSaved();
    } catch (e) {
      set((s) => ({ saved: { ...s.saved, error: parseApiError(e).message } }));
    }
  },

  reset: () =>
    set({
      items: { ...section(), data: [] },
      recommendations: section(),
      outfits: section(),
      saved: { ...section(), data: [] },
      uploading: false,
      uploadError: null,
    }),
}));

export default useWardrobeStore;
