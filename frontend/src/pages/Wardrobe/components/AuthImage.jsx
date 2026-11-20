import { useEffect, useState } from 'react';
import { wardrobeApi } from '../../../api';

/**
 * Wardrobe photos are served by an authenticated endpoint, so a plain <img src>
 * (which cannot send the Authorization header) would 401. Fetch as a blob instead.
 */
const AuthImage = ({ src, alt = '', className = '' }) => {
  const [objectUrl, setObjectUrl] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let created = null;
    wardrobeApi
      .getImage(src)
      .then(({ data }) => {
        if (cancelled) return;
        created = URL.createObjectURL(data);
        setObjectUrl(created);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
      if (created) URL.revokeObjectURL(created);
    };
  }, [src]);

  if (failed) return <div className={className} role="img" aria-label={`${alt} (image unavailable)`} />;
  if (!objectUrl) return <div className={className} aria-busy="true" />;
  return <img src={objectUrl} alt={alt} className={className} />;
};

export default AuthImage;
