import { useState, useRef } from 'react';
import { CSVPreview, CSVImportResult, campaignApi } from '../../lib/campaignApi';

interface CSVImportProps {
  campaignId: string;
  onSuccess: (result: CSVImportResult) => void;
  onCancel: () => void;
}

export function CSVImport({ campaignId, onSuccess, onCancel }: CSVImportProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CSVPreview | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'upload' | 'preview' | 'importing'>('upload');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      setError('Le fichier doit être au format CSV');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setLoading(true);

    try {
      const previewData = await campaignApi.previewCSV(campaignId, selectedFile);
      setPreview(previewData);
      setColumnMapping(previewData.column_mapping);
      setStep('preview');
    } catch (err: any) {
      setError(err.message || 'Erreur lors de la lecture du fichier');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setStep('importing');

    try {
      const result = await campaignApi.importCSV(campaignId, file, columnMapping);
      onSuccess(result);
    } catch (err: any) {
      setError(err.message || 'Erreur lors de l\'importation');
      setStep('preview');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setColumnMapping({});
    setStep('upload');
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="csv-import">
      <h2>Importer des destinataires (CSV)</h2>

      {error && <div className="error-message">{error}</div>}

      {step === 'upload' && (
        <div className="upload-section">
          <div className="file-input-wrapper">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              disabled={loading}
            />
            <button
              type="button"
              className="btn-secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
            >
              {loading ? 'Analyse en cours...' : 'Choisir un fichier CSV'}
            </button>
          </div>

          <div className="csv-instructions">
            <h3>Format attendu</h3>
            <p>Le fichier CSV doit contenir au minimum une colonne <strong>email</strong>.</p>
            <p>Colonnes optionnelles : first_name, last_name, company</p>
            <p>Exemple :</p>
            <pre>
              email,first_name,last_name,company{'\n'}
              jean.dupont@example.com,Jean,Dupont,Acme Corp{'\n'}
              marie.martin@example.com,Marie,Martin,Tech Inc
            </pre>
          </div>
        </div>
      )}

      {step === 'preview' && preview && (
        <div className="preview-section">
          <div className="preview-summary">
            <div className="summary-card">
              <div className="summary-label">Total de lignes</div>
              <div className="summary-value">{preview.total_rows}</div>
            </div>
            <div className="summary-card valid">
              <div className="summary-label">Lignes valides</div>
              <div className="summary-value">
                {preview.preview_rows.filter((r: { is_valid: boolean }) => r.is_valid).length} / {preview.preview_rows.length}
              </div>
            </div>
            <div className="summary-card invalid">
              <div className="summary-label">Lignes invalides</div>
              <div className="summary-value">
                {preview.preview_rows.filter((r: { is_valid: boolean }) => !r.is_valid).length}
              </div>
            </div>
          </div>

          <div className="column-mapping">
            <h3>Correspondance des colonnes</h3>
            <div className="mapping-grid">
              {Object.entries(columnMapping).map(([key, value]) => (
                <div key={key} className="mapping-item">
                  <span className="mapping-label">{key}</span>
                  <span className="mapping-arrow">→</span>
                  <span className="mapping-value">{value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="preview-table">
            <h3>Aperçu des données (10 premières lignes)</h3>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Email</th>
                  <th>Prénom</th>
                  <th>Nom</th>
                  <th>Société</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {preview.preview_rows.map((row: any) => (
                  <tr key={row.row_number} className={!row.is_valid ? 'invalid-row' : ''}>
                    <td>{row.row_number}</td>
                    <td>{row.email}</td>
                    <td>{row.first_name || '-'}</td>
                    <td>{row.last_name || '-'}</td>
                    <td>{row.company || '-'}</td>
                    <td>
                      {row.is_valid ? (
                        <span className="badge badge-success">✓ Valide</span>
                      ) : (
                        <span className="badge badge-error" title={row.error}>
                          ✗ {row.error}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="form-actions">
            <button onClick={handleReset} className="btn-secondary" disabled={loading}>
              Annuler
            </button>
            <button onClick={handleImport} className="btn-primary" disabled={loading}>
              {loading ? 'Importation...' : 'Confirmer l\'importation'}
            </button>
          </div>
        </div>
      )}

      {step === 'importing' && (
        <div className="importing-section">
          <div className="spinner"></div>
          <p>Importation en cours...</p>
        </div>
      )}
    </div>
  );
}
