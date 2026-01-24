import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Camera, Upload, Check, AlertCircle } from 'lucide-react';
import { useOnboardingStore } from '../../../store';
import { analysisApi } from '../../../api';
import Button from '../../../components/ui/Button';
import styles from './StepSelfie.module.css';

const StepSelfie = () => {
  const fileInputRef = useRef(null);
  const [preview, setPreview] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);

  const {
    isAnalyzing,
    setAnalyzing,
    setSelfieData,
    faceAnalysis,
    nextStep,
    setError: setStoreError,
  } = useOnboardingStore();

  const handleFileSelect = async (file) => {
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image size should be less than 10MB');
      return;
    }

    setError(null);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    // Analyze face
    setAnalyzing(true);
    try {
      const response = await analysisApi.analyzeFace(file);
      setSelfieData(preview, response.data);
    } catch (err) {
      const errorMessage =
        err.response?.data?.message || 'Failed to analyze image. Please try again.';
      setError(errorMessage);
      setStoreError(errorMessage);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={styles.step}>
      <div className={styles.header}>
        <h2 className={styles.title}>Let's Analyze Your Features</h2>
        <p className={styles.subtitle}>
          Upload a clear selfie so we can detect your skin tone, undertone, and
          facial features for personalized recommendations.
        </p>
      </div>

      <div className={styles.body}>
        {/* Upload Area */}
        <motion.div
          className={`${styles.uploadArea} ${dragActive ? styles.dragActive : ''} ${
            preview ? styles.hasPreview : ''
          } ${error ? styles.hasError : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={!preview ? triggerFileInput : undefined}
          whileHover={!preview ? { scale: 1.01 } : undefined}
          whileTap={!preview ? { scale: 0.99 } : undefined}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleInputChange}
            className={styles.fileInput}
          />

          {preview ? (
            <div className={styles.previewContainer}>
              <img src={preview} alt="Selfie preview" className={styles.preview} />
              {isAnalyzing && (
                <div className={styles.analyzing}>
                  <div className={styles.analyzingSpinner} />
                  <span>Analyzing your features...</span>
                </div>
              )}
              {faceAnalysis && !isAnalyzing && (
                <div className={styles.analysisComplete}>
                  <Check size={24} />
                  <span>Analysis complete!</span>
                </div>
              )}
            </div>
          ) : (
            <div className={styles.uploadPrompt}>
              <div className={styles.uploadIcon}>
                <Camera size={32} />
              </div>
              <p className={styles.uploadText}>
                Drag and drop your selfie here, or click to browse
              </p>
              <p className={styles.uploadHint}>
                PNG, JPG up to 10MB
              </p>
            </div>
          )}
        </motion.div>

        {/* Error message */}
        {error && (
          <div className={styles.error}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Analysis Results Preview */}
        {faceAnalysis && (
          <motion.div
            className={styles.analysisResults}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h4 className={styles.resultsTitle}>Detected Attributes</h4>
            <div className={styles.attributeGrid}>
              <div className={styles.attribute}>
                <span className={styles.attributeLabel}>Skin Tone</span>
                <div className={styles.attributeValue}>
                  <span
                    className={styles.colorSwatch}
                    style={{ backgroundColor: faceAnalysis.skinToneHex || '#D4A574' }}
                  />
                  <span>{faceAnalysis.skinTone || 'Medium Warm'}</span>
                </div>
              </div>
              <div className={styles.attribute}>
                <span className={styles.attributeLabel}>Undertone</span>
                <span className={styles.attributeValue}>
                  {faceAnalysis.undertone || 'Warm'}
                </span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Tips */}
        <div className={styles.tips}>
          <h4 className={styles.tipsTitle}>Tips for best results:</h4>
          <ul className={styles.tipsList}>
            <li>Use natural lighting</li>
            <li>Face the camera directly</li>
            <li>Avoid heavy makeup or filters</li>
          </ul>
        </div>
      </div>

      <div className={styles.actions}>
        {preview && (
          <Button variant="outline" onClick={triggerFileInput}>
            Upload Different Photo
          </Button>
        )}
        <Button
          onClick={nextStep}
          disabled={!faceAnalysis || isAnalyzing}
          loading={isAnalyzing}
        >
          {faceAnalysis ? 'Continue' : 'Analyzing...'}
        </Button>
      </div>
    </div>
  );
};

export default StepSelfie;
