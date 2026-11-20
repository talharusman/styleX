import { useState } from 'react';
import Modal from '../../../components/ui/Modal';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import { CATEGORIES, STYLES } from '../constants';
import styles from '../Wardrobe.module.css';


/** Lets the user confirm or correct what the classifier guessed. */
const ItemEditModal = ({ item, onClose, onSave }) => {
  const [form, setForm] = useState({
    name: item.name,
    category: item.category === 'unknown' ? '' : item.category,
    style: item.style,
    formality_level: item.formality_level,
    primary_color_name: item.primary_color.name,
    primary_color_hex: item.primary_color.hex_code,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.category) {
      setError('Choose a category so this item can be used in recommendations');
      return;
    }
    setSaving(true);
    setError(null);
    const result = await onSave(item.id, {
      name: form.name.trim() || undefined,
      category: form.category,
      style: form.style,
      formality_level: Number(form.formality_level),
      primary_color_name: form.primary_color_name.trim() || undefined,
      primary_color_hex: form.primary_color_hex,
    });
    setSaving(false);
    if (result.success) onClose();
    else setError(result.error);
  };

  return (
    <Modal isOpen onClose={onClose} title="Edit item" size="md">
      <form onSubmit={submit} className={styles.editForm}>
        {item.needs_review && (
          <p className={styles.reviewNote}>
            The analysis was not confident about this item. Please confirm the category and style.
          </p>
        )}
        <Input label="Name" aria-label="Name" value={form.name} onChange={set('name')} maxLength={100} />

        <label className={styles.field}>
          <span>Category</span>
          <select value={form.category} onChange={set('category')}>
            <option value="">Select…</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>Style</span>
          <select value={form.style} onChange={set('style')}>
            {STYLES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>

        <label className={styles.field}>
          <span>Formality: {form.formality_level}/10</span>
          <input type="range" min="1" max="10" value={form.formality_level} onChange={set('formality_level')} />
        </label>

        <div className={styles.colorRow}>
          <Input label="Main colour" aria-label="Main colour name" value={form.primary_color_name} onChange={set('primary_color_name')} maxLength={40} />
          <input
            type="color"
            aria-label="Main colour"
            value={form.primary_color_hex}
            onChange={set('primary_color_hex')}
            className={styles.colorPicker}
          />
        </div>

        {error && <div className={styles.errorBox} role="alert">{error}</div>}

        <div className={styles.modalActions}>
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" loading={saving}>Save</Button>
        </div>
      </form>
    </Modal>
  );
};

export default ItemEditModal;
