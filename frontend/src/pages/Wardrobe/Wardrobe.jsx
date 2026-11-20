import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, Plus, Trash2, Pencil, AlertTriangle, Bookmark, BookmarkCheck, Loader2 } from 'lucide-react';
import { useWardrobeStore } from '../../store';
import { Header } from '../../components/layout';
import Button from '../../components/ui/Button';
import AuthImage from './components/AuthImage';
import ItemEditModal from './components/ItemEditModal';
import { CATEGORIES } from './constants';
import styles from './Wardrobe.module.css';

const TABS = [
  { id: 'recommended', label: 'Recommended' },
  { id: 'outfits', label: 'Outfits' },
  { id: 'wardrobe', label: 'My wardrobe' },
  { id: 'saved', label: 'Saved' },
];

const pct = (n) => `${Math.round(n * 100)}%`;

const Section = ({ state, empty, children }) => {
  if (state.loading && !state.data) {
    return <div className={styles.state} role="status"><Loader2 className={styles.spin} size={20} /> Loading…</div>;
  }
  if (state.error) {
    if (state.errorCode === 'profile_incomplete') {
      return (
        <div className={styles.state}>
          <p>Recommendations need your skin analysis first.</p>
          <Button variant="primary" to="/onboarding">Analyze my selfie</Button>
        </div>
      );
    }
    return <div className={styles.errorBox} role="alert">{state.error}</div>;
  }
  if (empty) return <div className={styles.state}>{empty}</div>;
  return children;
};

const Swatch = ({ color }) => (
  <span className={styles.swatch} style={{ background: color.hex_code }} title={color.name} />
);

const ItemThumb = ({ item }) => <AuthImage src={item.image_url} alt={item.name} className={styles.thumb} />;

const Wardrobe = () => {
  const store = useWardrobeStore();
  const { items, recommendations, outfits, saved, uploading, uploadError } = store;
  const [tab, setTab] = useState('recommended');
  const [category, setCategory] = useState('');
  const [onlyFavorites, setOnlyFavorites] = useState(false);
  const [editing, setEditing] = useState(null);
  const [notice, setNotice] = useState(null);
  const fileRef = useRef(null);

  const { fetchItems, fetchRecommendations, fetchOutfits, fetchSaved } = store;
  useEffect(() => {
    fetchItems();
    fetchRecommendations();
    fetchOutfits();
    fetchSaved();
  }, [fetchItems, fetchRecommendations, fetchOutfits, fetchSaved]);

  const onFiles = async (e) => {
    const files = Array.from(e.target.files || []);
    e.target.value = '';
    for (const file of files) {
      const result = await store.uploadItem(file);
      if (!result.success) break; // uploadError is shown below
    }
    setTab('wardrobe');
  };

  const savedKeys = new Set((saved.data || []).map((o) => o.items.map((i) => i.id).sort().join('|')));
  const isSaved = (outfit) => savedKeys.has(outfit.items.map((r) => r.item.id).sort().join('|'));

  const visibleItems = (items.data || []).filter(
    (i) => (!category || i.category === category) && (!onlyFavorites || i.is_favorite)
  );
  const needsReview = (items.data || []).filter((i) => i.needs_review).length;

  const save = async (outfit) => {
    const result = await store.saveOutfit(outfit);
    setNotice(result.success ? 'Outfit saved' : result.error);
  };

  const remove = async (item) => {
    if (!window.confirm(`Delete "${item.name}" from your wardrobe?`)) return;
    const result = await store.deleteItem(item.id);
    if (!result.success) setNotice(result.error);
  };

  const rec = recommendations.data;

  return (
    <div className={styles.page}>
      <Header />
      <main className={styles.main}>
        <div className={styles.container}>
          <div className={styles.titleRow}>
            <div>
              <h1 className={styles.title}>Your wardrobe</h1>
              <p className={styles.subtitle}>
                Upload clothes you own. We rank them against your skin tone and preferences.
              </p>
            </div>
            <div>
              <input ref={fileRef} type="file" accept="image/*" multiple hidden onChange={onFiles} aria-label="Upload clothing photos" />
              <Button variant="primary" icon={<Plus size={18} />} loading={uploading} onClick={() => fileRef.current?.click()}>
                Add clothing
              </Button>
            </div>
          </div>

          {uploading && <div className={styles.state} role="status">Analyzing your photo… the first one can take a little longer.</div>}
          {uploadError && <div className={styles.errorBox} role="alert">{uploadError}</div>}
          {notice && <div className={styles.notice} role="status" onAnimationEnd={() => setNotice(null)}>{notice}</div>}
          {needsReview > 0 && tab !== 'wardrobe' && (
            <button type="button" className={styles.reviewBanner} onClick={() => setTab('wardrobe')}>
              <AlertTriangle size={16} /> {needsReview} item{needsReview > 1 ? 's' : ''} need a quick review. Confirm category and style for better results.
            </button>
          )}

          <div className={styles.tabs} role="tablist">
            {TABS.map((t) => (
              <button key={t.id} role="tab" aria-selected={tab === t.id}
                className={`${styles.tab} ${tab === t.id ? styles.tabActive : ''}`} onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'recommended' && (
            <Section
              state={recommendations}
              empty={rec && rec.recommendations.length === 0 && (
                rec.reason === 'empty_wardrobe'
                  ? 'Your wardrobe is empty. Add a few photos of your clothes to get recommendations.'
                  : 'None of your items have a confirmed category yet. Review them in "My wardrobe".'
              )}
            >
              {rec && (
                <>
                  <div className={styles.paletteBar}>
                    <span>{rec.detected_season} season · {rec.undertone} undertone</span>
                    <span className={styles.palette}>Best colours: {rec.best_colors.slice(0, 6).join(', ')}</span>
                  </div>
                  <ol className={styles.rankList}>
                    {rec.recommendations.map((r) => (
                      <li key={r.item.id} className={styles.rankCard}>
                        <span className={styles.rank}>{r.rank}</span>
                        <ItemThumb item={r.item} />
                        <div className={styles.rankBody}>
                          <div className={styles.rankHead}>
                            <strong>{r.item.name}</strong>
                            <span className={styles.score}>{pct(r.overall_score)} · {r.recommendation_level}</span>
                          </div>
                          <p className={styles.reasoning}>{r.reasoning}</p>
                          <div className={styles.meta}>
                            <Swatch color={r.item.primary_color} /> {r.item.primary_color.name} · {r.item.category} · {r.item.style}
                            <span className={styles.breakdown}>
                              colour {pct(r.color_score)} · style {pct(r.style_score)} · formality {pct(r.formality_score)}
                            </span>
                          </div>
                        </div>
                        <button className={styles.iconBtn} aria-label={r.item.is_favorite ? 'Remove favorite' : 'Add favorite'}
                          onClick={() => store.toggleFavorite(r.item.id)}>
                          <Heart size={18} fill={r.item.is_favorite ? 'currentColor' : 'none'} />
                        </button>
                      </li>
                    ))}
                  </ol>
                  {rec.excluded_needs_review > 0 && (
                    <p className={styles.hint}>{rec.excluded_needs_review} item(s) were skipped because their category is unknown.</p>
                  )}
                </>
              )}
            </Section>
          )}

          {tab === 'outfits' && (
            <Section
              state={outfits}
              empty={outfits.data && outfits.data.outfits.length === 0 && 'Add at least one top and one bottom (or a dress) to see complete outfits.'}
            >
              <div className={styles.outfitGrid}>
                {(outfits.data?.outfits || []).map((o) => (
                  <article key={o.outfit_id} className={styles.outfitCard}>
                    <div className={styles.outfitImages}>
                      {o.items.map((r) => <ItemThumb key={r.item.id} item={r.item} />)}
                    </div>
                    <div className={styles.rankHead}>
                      <strong>{o.items.map((r) => r.item.name).join(' + ')}</strong>
                      <span className={styles.score}>{pct(o.outfit_score)}</span>
                    </div>
                    <p className={styles.reasoning}>{o.reasoning}</p>
                    <Button size="sm" variant={isSaved(o) ? 'ghost' : 'outline'} disabled={isSaved(o)}
                      icon={isSaved(o) ? <BookmarkCheck size={16} /> : <Bookmark size={16} />} onClick={() => save(o)}>
                      {isSaved(o) ? 'Saved' : 'Save outfit'}
                    </Button>
                  </article>
                ))}
              </div>
            </Section>
          )}

          {tab === 'wardrobe' && (
            <Section state={items} empty={items.data && items.data.length === 0 && 'Nothing here yet. Use "Add clothing" to upload your first item.'}>
              <div className={styles.filters}>
                <button className={`${styles.chip} ${!category ? styles.chipActive : ''}`} onClick={() => setCategory('')}>All</button>
                {CATEGORIES.map((c) => (
                  <button key={c} className={`${styles.chip} ${category === c ? styles.chipActive : ''}`} onClick={() => setCategory(c)}>{c}</button>
                ))}
                <button className={`${styles.chip} ${onlyFavorites ? styles.chipActive : ''}`} onClick={() => setOnlyFavorites((v) => !v)}>
                  <Heart size={12} /> Favorites
                </button>
              </div>
              <div className={styles.itemGrid}>
                {visibleItems.map((i) => (
                  <article key={i.id} className={styles.itemCard}>
                    <ItemThumb item={i} />
                    {i.needs_review && <span className={styles.badge}><AlertTriangle size={12} /> Review</span>}
                    <div className={styles.itemInfo}>
                      <strong>{i.name}</strong>
                      <span className={styles.meta}><Swatch color={i.primary_color} /> {i.category} · {i.style}</span>
                    </div>
                    <div className={styles.itemActions}>
                      <button className={styles.iconBtn} aria-label={i.is_favorite ? 'Remove favorite' : 'Add favorite'} onClick={() => store.toggleFavorite(i.id)}>
                        <Heart size={16} fill={i.is_favorite ? 'currentColor' : 'none'} />
                      </button>
                      <button className={styles.iconBtn} aria-label={`Edit ${i.name}`} onClick={() => setEditing(i)}><Pencil size={16} /></button>
                      <button className={styles.iconBtn} aria-label={`Delete ${i.name}`} onClick={() => remove(i)}><Trash2 size={16} /></button>
                    </div>
                  </article>
                ))}
              </div>
              {visibleItems.length === 0 && items.data?.length > 0 && <div className={styles.state}>No items match these filters.</div>}
            </Section>
          )}

          {tab === 'saved' && (
            <Section state={saved} empty={saved.data && saved.data.length === 0 && <>No saved outfits yet. Save one from the <Link to="#" onClick={(e) => { e.preventDefault(); setTab('outfits'); }}>Outfits</Link> tab.</>}>
              <div className={styles.outfitGrid}>
                {(saved.data || []).map((o) => (
                  <article key={o.id} className={styles.outfitCard}>
                    <div className={styles.outfitImages}>
                      {o.items.map((i) => <ItemThumb key={i.id} item={i} />)}
                    </div>
                    <div className={styles.rankHead}>
                      <strong>{o.name}</strong>
                      {o.score > 0 && <span className={styles.score}>{pct(o.score)}</span>}
                    </div>
                    {o.reasoning && <p className={styles.reasoning}>{o.reasoning}</p>}
                    <Button size="sm" variant="ghost" icon={<Trash2 size={16} />} onClick={() => store.deleteSavedOutfit(o.id)}>Remove</Button>
                  </article>
                ))}
              </div>
            </Section>
          )}
        </div>
      </main>

      {editing && (
        <ItemEditModal item={editing} onClose={() => setEditing(null)} onSave={store.updateItem} />
      )}
    </div>
  );
};

export default Wardrobe;
