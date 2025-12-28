import { useRef, useState, useEffect, useCallback } from 'react';

interface EditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  minHeight?: string;
  variables?: string[];
}

/**
 * Simple WYSIWYG Email Editor
 * 
 * A lightweight rich text editor for email content with:
 * - Basic formatting (bold, italic, underline)
 * - Links and images
 * - Variable insertion
 * - HTML source view
 * - Responsive preview
 */
export function EmailEditor({
  value,
  onChange,
  placeholder = 'Composez votre email...',
  minHeight = '400px',
  variables = ['firstname', 'lastname', 'company', 'unsubscribe_url'],
}: EditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [isSourceView, setIsSourceView] = useState(false);
  const [sourceCode, setSourceCode] = useState(value);
  const [showVariables, setShowVariables] = useState(false);
  const [previewMode, setPreviewMode] = useState<'desktop' | 'mobile'>('desktop');

  // Sync external value changes
  useEffect(() => {
    if (isSourceView) {
      setSourceCode(value);
    } else if (editorRef.current && editorRef.current.innerHTML !== value) {
      editorRef.current.innerHTML = value;
    }
  }, [value, isSourceView]);

  // Handle content changes
  const handleInput = useCallback(() => {
    if (editorRef.current) {
      const newValue = editorRef.current.innerHTML;
      onChange(newValue);
    }
  }, [onChange]);

  // Handle source code changes
  const handleSourceChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setSourceCode(e.target.value);
    onChange(e.target.value);
  }, [onChange]);

  // Toggle source view
  const toggleSourceView = useCallback(() => {
    if (isSourceView) {
      // Switching to WYSIWYG
      if (editorRef.current) {
        editorRef.current.innerHTML = sourceCode;
      }
    } else {
      // Switching to source
      setSourceCode(editorRef.current?.innerHTML || value);
    }
    setIsSourceView(!isSourceView);
  }, [isSourceView, sourceCode, value]);

  // Execute formatting command
  const execCommand = useCallback((command: string, value: string | undefined = undefined) => {
    document.execCommand(command, false, value);
    editorRef.current?.focus();
    handleInput();
  }, [handleInput]);

  // Insert variable
  const insertVariable = useCallback((variable: string) => {
    const variableHtml = `<span class="variable" contenteditable="false">{{${variable}}}</span>`;
    execCommand('insertHTML', variableHtml);
    setShowVariables(false);
  }, [execCommand]);

  // Insert link
  const insertLink = useCallback(() => {
    const url = prompt('URL du lien:', 'https://');
    if (url) {
      execCommand('createLink', url);
    }
  }, [execCommand]);

  // Insert image
  const insertImage = useCallback(() => {
    const url = prompt('URL de l\'image:', 'https://');
    if (url) {
      execCommand('insertImage', url);
    }
  }, [execCommand]);

  return (
    <div className="email-editor">
      {/* Toolbar */}
      <div className="editor-toolbar">
        <div className="toolbar-group">
          <button
            type="button"
            onClick={() => execCommand('bold')}
            title="Gras (Ctrl+B)"
            className="toolbar-btn"
          >
            <strong>B</strong>
          </button>
          <button
            type="button"
            onClick={() => execCommand('italic')}
            title="Italique (Ctrl+I)"
            className="toolbar-btn"
          >
            <em>I</em>
          </button>
          <button
            type="button"
            onClick={() => execCommand('underline')}
            title="Souligné (Ctrl+U)"
            className="toolbar-btn"
          >
            <u>U</u>
          </button>
        </div>

        <div className="toolbar-separator" />

        <div className="toolbar-group">
          <button
            type="button"
            onClick={() => execCommand('justifyLeft')}
            title="Aligner à gauche"
            className="toolbar-btn"
          >
            ⬅
          </button>
          <button
            type="button"
            onClick={() => execCommand('justifyCenter')}
            title="Centrer"
            className="toolbar-btn"
          >
            ⬌
          </button>
          <button
            type="button"
            onClick={() => execCommand('justifyRight')}
            title="Aligner à droite"
            className="toolbar-btn"
          >
            ➡
          </button>
        </div>

        <div className="toolbar-separator" />

        <div className="toolbar-group">
          <button
            type="button"
            onClick={() => execCommand('insertUnorderedList')}
            title="Liste à puces"
            className="toolbar-btn"
          >
            • ─
          </button>
          <button
            type="button"
            onClick={() => execCommand('insertOrderedList')}
            title="Liste numérotée"
            className="toolbar-btn"
          >
            1. ─
          </button>
        </div>

        <div className="toolbar-separator" />

        <div className="toolbar-group">
          <button
            type="button"
            onClick={insertLink}
            title="Insérer un lien"
            className="toolbar-btn"
          >
            🔗
          </button>
          <button
            type="button"
            onClick={insertImage}
            title="Insérer une image"
            className="toolbar-btn"
          >
            🖼
          </button>
        </div>

        <div className="toolbar-separator" />

        <div className="toolbar-group">
          <select
            onChange={(e) => execCommand('formatBlock', e.target.value)}
            className="toolbar-select"
            defaultValue=""
          >
            <option value="">Format</option>
            <option value="h1">Titre 1</option>
            <option value="h2">Titre 2</option>
            <option value="h3">Titre 3</option>
            <option value="p">Paragraphe</option>
          </select>
        </div>

        <div className="toolbar-separator" />

        <div className="toolbar-group">
          <div className="variable-dropdown">
            <button
              type="button"
              onClick={() => setShowVariables(!showVariables)}
              className="toolbar-btn"
              title="Insérer une variable"
            >
              {'{{'} var {'}}'}
            </button>
            {showVariables && (
              <div className="variable-menu">
                {variables.map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => insertVariable(v)}
                    className="variable-item"
                  >
                    {`{{${v}}}`}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="toolbar-right">
          <div className="toolbar-group">
            <button
              type="button"
              onClick={() => setPreviewMode('desktop')}
              className={`toolbar-btn ${previewMode === 'desktop' ? 'active' : ''}`}
              title="Vue desktop"
            >
              🖥
            </button>
            <button
              type="button"
              onClick={() => setPreviewMode('mobile')}
              className={`toolbar-btn ${previewMode === 'mobile' ? 'active' : ''}`}
              title="Vue mobile"
            >
              📱
            </button>
          </div>

          <div className="toolbar-separator" />

          <button
            type="button"
            onClick={toggleSourceView}
            className={`toolbar-btn ${isSourceView ? 'active' : ''}`}
            title="Code source"
          >
            {'</>'}
          </button>
        </div>
      </div>

      {/* Editor Content */}
      <div className={`editor-content ${previewMode === 'mobile' ? 'mobile-preview' : ''}`}>
        {isSourceView ? (
          <textarea
            value={sourceCode}
            onChange={handleSourceChange}
            className="source-editor"
            style={{ minHeight }}
            spellCheck={false}
          />
        ) : (
          <div
            ref={editorRef}
            contentEditable
            className="wysiwyg-editor"
            style={{ minHeight }}
            onInput={handleInput}
            onBlur={handleInput}
            data-placeholder={placeholder}
            dangerouslySetInnerHTML={{ __html: value }}
          />
        )}
      </div>

      <style>{`
        .email-editor {
          border: 1px solid var(--border-color, #ddd);
          border-radius: 8px;
          overflow: hidden;
          background: var(--bg-color, #fff);
        }

        .editor-toolbar {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
          padding: 8px;
          background: var(--toolbar-bg, #f5f5f5);
          border-bottom: 1px solid var(--border-color, #ddd);
          align-items: center;
        }

        .toolbar-group {
          display: flex;
          gap: 2px;
        }

        .toolbar-separator {
          width: 1px;
          height: 24px;
          background: var(--border-color, #ddd);
          margin: 0 4px;
        }

        .toolbar-right {
          margin-left: auto;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .toolbar-btn {
          padding: 6px 10px;
          border: none;
          background: transparent;
          cursor: pointer;
          border-radius: 4px;
          font-size: 14px;
          color: var(--text-color, #333);
          transition: background 0.2s;
        }

        .toolbar-btn:hover {
          background: var(--hover-bg, #e0e0e0);
        }

        .toolbar-btn.active {
          background: var(--active-bg, #d0d0d0);
        }

        .toolbar-select {
          padding: 4px 8px;
          border: 1px solid var(--border-color, #ddd);
          border-radius: 4px;
          background: var(--bg-color, #fff);
          font-size: 12px;
        }

        .variable-dropdown {
          position: relative;
        }

        .variable-menu {
          position: absolute;
          top: 100%;
          left: 0;
          background: var(--bg-color, #fff);
          border: 1px solid var(--border-color, #ddd);
          border-radius: 4px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          z-index: 100;
          min-width: 150px;
        }

        .variable-item {
          display: block;
          width: 100%;
          padding: 8px 12px;
          border: none;
          background: none;
          text-align: left;
          cursor: pointer;
          font-family: monospace;
          font-size: 12px;
        }

        .variable-item:hover {
          background: var(--hover-bg, #f0f0f0);
        }

        .editor-content {
          transition: max-width 0.3s;
        }

        .editor-content.mobile-preview {
          max-width: 375px;
          margin: 0 auto;
          border-left: 1px solid var(--border-color, #ddd);
          border-right: 1px solid var(--border-color, #ddd);
        }

        .wysiwyg-editor {
          padding: 16px;
          outline: none;
          line-height: 1.6;
          overflow-y: auto;
        }

        .wysiwyg-editor:empty:before {
          content: attr(data-placeholder);
          color: var(--placeholder-color, #999);
          pointer-events: none;
        }

        .wysiwyg-editor .variable {
          background: var(--variable-bg, #e3f2fd);
          color: var(--variable-color, #1976d2);
          padding: 2px 6px;
          border-radius: 4px;
          font-family: monospace;
          font-size: 0.9em;
        }

        .wysiwyg-editor img {
          max-width: 100%;
          height: auto;
        }

        .source-editor {
          width: 100%;
          padding: 16px;
          border: none;
          resize: vertical;
          font-family: monospace;
          font-size: 13px;
          line-height: 1.5;
          background: var(--source-bg, #1e1e1e);
          color: var(--source-color, #d4d4d4);
        }

        /* Dark mode */
        [data-theme="dark"] .email-editor {
          --bg-color: #1a1a2e;
          --toolbar-bg: #16213e;
          --border-color: #3d3d5c;
          --text-color: #e0e0e0;
          --hover-bg: #2a2a4a;
          --active-bg: #3a3a5a;
          --placeholder-color: #666;
          --variable-bg: #1e3a5f;
          --variable-color: #64b5f6;
          --source-bg: #0d0d1a;
          --source-color: #e0e0e0;
        }
      `}</style>
    </div>
  );
}

export default EmailEditor;
