import { useState, useCallback } from 'react';

type Language = 'fr' | 'en' | 'es' | 'de';

interface Translations {
  [key: string]: {
    [lang in Language]: string;
  };
}

const translations: Translations = {
  // Navigation & Headers
  'app.title': {
    fr: 'Gestion des Campagnes Email',
    en: 'Email Campaign Manager',
    es: 'Gestor de Campañas de Email',
    de: 'E-Mail-Kampagnen-Manager',
  },
  'app.subtitle': {
    fr: 'Créez et gérez vos campagnes d\'emailing à grande échelle',
    en: 'Create and manage your email campaigns at scale',
    es: 'Crea y gestiona tus campañas de email a gran escala',
    de: 'Erstellen und verwalten Sie Ihre E-Mail-Kampagnen im großen Stil',
  },

  // Buttons
  'button.create': {
    fr: 'Nouvelle campagne',
    en: 'New campaign',
    es: 'Nueva campaña',
    de: 'Neue Kampagne',
  },
  'button.edit': {
    fr: 'Modifier',
    en: 'Edit',
    es: 'Editar',
    de: 'Bearbeiten',
  },
  'button.delete': {
    fr: 'Supprimer',
    en: 'Delete',
    es: 'Eliminar',
    de: 'Löschen',
  },
  'button.save': {
    fr: 'Enregistrer',
    en: 'Save',
    es: 'Guardar',
    de: 'Speichern',
  },
  'button.cancel': {
    fr: 'Annuler',
    en: 'Cancel',
    es: 'Cancelar',
    de: 'Abbrechen',
  },
  'button.send': {
    fr: 'Envoyer',
    en: 'Send',
    es: 'Enviar',
    de: 'Senden',
  },
  'button.duplicate': {
    fr: 'Dupliquer',
    en: 'Duplicate',
    es: 'Duplicar',
    de: 'Duplizieren',
  },
  'button.preview': {
    fr: 'Aperçu',
    en: 'Preview',
    es: 'Vista previa',
    de: 'Vorschau',
  },
  'button.import': {
    fr: 'Importer CSV',
    en: 'Import CSV',
    es: 'Importar CSV',
    de: 'CSV importieren',
  },
  'button.export': {
    fr: 'Exporter',
    en: 'Export',
    es: 'Exportar',
    de: 'Exportieren',
  },
  'button.schedule': {
    fr: 'Planifier',
    en: 'Schedule',
    es: 'Programar',
    de: 'Planen',
  },
  'button.pause': {
    fr: 'Pause',
    en: 'Pause',
    es: 'Pausar',
    de: 'Pausieren',
  },
  'button.resume': {
    fr: 'Reprendre',
    en: 'Resume',
    es: 'Reanudar',
    de: 'Fortsetzen',
  },

  // Campaign Status
  'status.draft': {
    fr: 'Brouillon',
    en: 'Draft',
    es: 'Borrador',
    de: 'Entwurf',
  },
  'status.scheduled': {
    fr: 'Planifiée',
    en: 'Scheduled',
    es: 'Programada',
    de: 'Geplant',
  },
  'status.sending': {
    fr: 'En cours',
    en: 'Sending',
    es: 'Enviando',
    de: 'Wird gesendet',
  },
  'status.paused': {
    fr: 'En pause',
    en: 'Paused',
    es: 'Pausada',
    de: 'Pausiert',
  },
  'status.completed': {
    fr: 'Terminée',
    en: 'Completed',
    es: 'Completada',
    de: 'Abgeschlossen',
  },
  'status.failed': {
    fr: 'Échec',
    en: 'Failed',
    es: 'Fallida',
    de: 'Fehlgeschlagen',
  },

  // Form Labels
  'form.name': {
    fr: 'Nom de la campagne',
    en: 'Campaign name',
    es: 'Nombre de la campaña',
    de: 'Kampagnenname',
  },
  'form.subject': {
    fr: 'Objet',
    en: 'Subject',
    es: 'Asunto',
    de: 'Betreff',
  },
  'form.fromName': {
    fr: 'Nom de l\'expéditeur',
    en: 'From name',
    es: 'Nombre del remitente',
    de: 'Absendername',
  },
  'form.fromEmail': {
    fr: 'Email de l\'expéditeur',
    en: 'From email',
    es: 'Email del remitente',
    de: 'Absender-E-Mail',
  },
  'form.replyTo': {
    fr: 'Répondre à',
    en: 'Reply to',
    es: 'Responder a',
    de: 'Antwort an',
  },
  'form.content': {
    fr: 'Contenu HTML',
    en: 'HTML content',
    es: 'Contenido HTML',
    de: 'HTML-Inhalt',
  },

  // Statistics
  'stats.recipients': {
    fr: 'Destinataires',
    en: 'Recipients',
    es: 'Destinatarios',
    de: 'Empfänger',
  },
  'stats.sent': {
    fr: 'Envoyés',
    en: 'Sent',
    es: 'Enviados',
    de: 'Gesendet',
  },
  'stats.opened': {
    fr: 'Ouverts',
    en: 'Opened',
    es: 'Abiertos',
    de: 'Geöffnet',
  },
  'stats.clicked': {
    fr: 'Cliqués',
    en: 'Clicked',
    es: 'Clicados',
    de: 'Geklickt',
  },
  'stats.failed': {
    fr: 'Échecs',
    en: 'Failed',
    es: 'Fallidos',
    de: 'Fehlgeschlagen',
  },
  'stats.unsubscribed': {
    fr: 'Désinscrits',
    en: 'Unsubscribed',
    es: 'Cancelados',
    de: 'Abgemeldet',
  },
  'stats.openRate': {
    fr: 'Taux d\'ouverture',
    en: 'Open rate',
    es: 'Tasa de apertura',
    de: 'Öffnungsrate',
  },
  'stats.clickRate': {
    fr: 'Taux de clic',
    en: 'Click rate',
    es: 'Tasa de clic',
    de: 'Klickrate',
  },
  'stats.bounceRate': {
    fr: 'Taux de rebond',
    en: 'Bounce rate',
    es: 'Tasa de rebote',
    de: 'Bounce-Rate',
  },

  // Messages
  'message.loading': {
    fr: 'Chargement...',
    en: 'Loading...',
    es: 'Cargando...',
    de: 'Laden...',
  },
  'message.noData': {
    fr: 'Aucune donnée',
    en: 'No data',
    es: 'Sin datos',
    de: 'Keine Daten',
  },
  'message.noCampaigns': {
    fr: 'Aucune campagne',
    en: 'No campaigns',
    es: 'Sin campañas',
    de: 'Keine Kampagnen',
  },
  'message.confirmDelete': {
    fr: 'Êtes-vous sûr de vouloir supprimer cette campagne ?',
    en: 'Are you sure you want to delete this campaign?',
    es: '¿Está seguro de que desea eliminar esta campaña?',
    de: 'Sind Sie sicher, dass Sie diese Kampagne löschen möchten?',
  },
  'message.success': {
    fr: 'Opération réussie',
    en: 'Operation successful',
    es: 'Operación exitosa',
    de: 'Vorgang erfolgreich',
  },
  'message.error': {
    fr: 'Une erreur est survenue',
    en: 'An error occurred',
    es: 'Se produjo un error',
    de: 'Ein Fehler ist aufgetreten',
  },

  // Import
  'import.title': {
    fr: 'Importer des destinataires',
    en: 'Import recipients',
    es: 'Importar destinatarios',
    de: 'Empfänger importieren',
  },
  'import.dropzone': {
    fr: 'Glissez un fichier CSV ici ou cliquez pour sélectionner',
    en: 'Drag a CSV file here or click to select',
    es: 'Arrastre un archivo CSV aquí o haga clic para seleccionar',
    de: 'Ziehen Sie eine CSV-Datei hierher oder klicken Sie zur Auswahl',
  },
  'import.validRows': {
    fr: 'Lignes valides',
    en: 'Valid rows',
    es: 'Filas válidas',
    de: 'Gültige Zeilen',
  },
  'import.invalidRows': {
    fr: 'Lignes invalides',
    en: 'Invalid rows',
    es: 'Filas inválidas',
    de: 'Ungültige Zeilen',
  },
  'import.duplicates': {
    fr: 'Doublons ignorés',
    en: 'Duplicates ignored',
    es: 'Duplicados ignorados',
    de: 'Duplikate ignoriert',
  },

  // Filters
  'filter.allStatus': {
    fr: 'Tous les statuts',
    en: 'All statuses',
    es: 'Todos los estados',
    de: 'Alle Status',
  },
  'filter.search': {
    fr: 'Rechercher...',
    en: 'Search...',
    es: 'Buscar...',
    de: 'Suchen...',
  },

  // A/B Testing
  'abtest.title': {
    fr: 'Test A/B',
    en: 'A/B Test',
    es: 'Prueba A/B',
    de: 'A/B-Test',
  },
  'abtest.variantA': {
    fr: 'Variante A',
    en: 'Variant A',
    es: 'Variante A',
    de: 'Variante A',
  },
  'abtest.variantB': {
    fr: 'Variante B',
    en: 'Variant B',
    es: 'Variante B',
    de: 'Variante B',
  },
  'abtest.winner': {
    fr: 'Gagnant',
    en: 'Winner',
    es: 'Ganador',
    de: 'Gewinner',
  },
  'abtest.confidence': {
    fr: 'Niveau de confiance',
    en: 'Confidence level',
    es: 'Nivel de confianza',
    de: 'Konfidenzniveau',
  },

  // Analytics
  'analytics.title': {
    fr: 'Statistiques',
    en: 'Analytics',
    es: 'Estadísticas',
    de: 'Analytik',
  },
  'analytics.heatmap': {
    fr: 'Carte thermique',
    en: 'Heatmap',
    es: 'Mapa de calor',
    de: 'Heatmap',
  },
  'analytics.byDomain': {
    fr: 'Par domaine',
    en: 'By domain',
    es: 'Por dominio',
    de: 'Nach Domain',
  },
  'analytics.trends': {
    fr: 'Tendances',
    en: 'Trends',
    es: 'Tendencias',
    de: 'Trends',
  },

  // Settings
  'settings.title': {
    fr: 'Paramètres',
    en: 'Settings',
    es: 'Configuración',
    de: 'Einstellungen',
  },
  'settings.language': {
    fr: 'Langue',
    en: 'Language',
    es: 'Idioma',
    de: 'Sprache',
  },
  'settings.theme': {
    fr: 'Thème',
    en: 'Theme',
    es: 'Tema',
    de: 'Thema',
  },
  'settings.dark': {
    fr: 'Sombre',
    en: 'Dark',
    es: 'Oscuro',
    de: 'Dunkel',
  },
  'settings.light': {
    fr: 'Clair',
    en: 'Light',
    es: 'Claro',
    de: 'Hell',
  },
};

// Get browser language
const getBrowserLanguage = (): Language => {
  const browserLang = navigator.language.split('-')[0];
  if (['fr', 'en', 'es', 'de'].includes(browserLang)) {
    return browserLang as Language;
  }
  return 'fr'; // Default to French
};

// Get stored language
const getStoredLanguage = (): Language => {
  const stored = localStorage.getItem('app_language');
  if (stored && ['fr', 'en', 'es', 'de'].includes(stored)) {
    return stored as Language;
  }
  return getBrowserLanguage();
};

// Translation hook
export function useTranslation() {
  const [language, setLanguageState] = useState<Language>(getStoredLanguage());

  const setLanguage = useCallback((lang: Language) => {
    localStorage.setItem('app_language', lang);
    setLanguageState(lang);
  }, []);

  const t = useCallback((key: string, params?: Record<string, string>): string => {
    const translation = translations[key]?.[language] || key;
    
    if (params) {
      return Object.entries(params).reduce(
        (acc, [k, v]) => acc.replace(`{{${k}}}`, v),
        translation
      );
    }
    
    return translation;
  }, [language]);

  return {
    t,
    language,
    setLanguage,
    availableLanguages: ['fr', 'en', 'es', 'de'] as Language[],
  };
}

// Language names for display
export const languageNames: Record<Language, string> = {
  fr: 'Français',
  en: 'English',
  es: 'Español',
  de: 'Deutsch',
};

export type { Language };
