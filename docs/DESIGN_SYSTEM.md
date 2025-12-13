# Design System Reception - Glassmorphism

## 🎨 Vue d'ensemble

Ce design system implémente le style **Glassmorphism** avec la palette de couleurs **Almadia** (Vert #005960 et Jaune #FFC73B). Il fournit un ensemble complet de composants React réutilisables et de styles CSS pour une interface moderne et élégante.

## 📦 Structure

```
app/core/shared/
├── components/          # Composants React réutilisables
│   ├── GlassCard.tsx
│   ├── GlassButton.tsx
│   ├── GlassInput.tsx
│   ├── SearchBox.tsx
│   ├── Toast.tsx
│   ├── Toggle.tsx
│   ├── Tag.tsx
│   ├── Tabs.tsx
│   ├── ProgressBar.tsx
│   ├── Spinner.tsx
│   ├── Alert.tsx
│   ├── Skeleton.tsx
│   ├── Stepper.tsx
│   ├── Modal.tsx
│   └── index.ts
└── styles/
    └── App.css          # Styles globaux et variables CSS
```

## 🎨 Palette de Couleurs

### Couleurs principales
- **Vert Almadia**: `rgb(0, 89, 96)` - #005960
- **Jaune Almadia**: `rgb(255, 199, 59)` - #FFC73B

### Variantes
- **Vert Léger**: `rgba(0, 89, 96, 0.1)` - Backgrounds
- **Jaune Léger**: `rgba(255, 199, 59, 0.1)` - Backgrounds
- **Vert Moyen**: `rgba(0, 89, 96, 0.8)` - Boutons
- **Jaune Moyen**: `rgb(255, 180, 59)` - Badges

### Gradients
```css
/* Principal */
linear-gradient(135deg, rgb(0, 89, 96), rgb(255, 199, 59))

/* Subtil */
linear-gradient(135deg, rgba(0, 89, 96, 0.1), rgba(255, 199, 59, 0.1))

/* Boutons */
linear-gradient(135deg, rgb(0, 89, 96), rgba(0, 89, 96, 0.8))

/* Horizontal */
linear-gradient(90deg, rgb(0, 89, 96), rgb(255, 199, 59))
```

## 🧩 Composants

### GlassCard
Carte avec effet glassmorphism.

```tsx
import { GlassCard } from '@/core/shared/components';

<GlassCard>
  <h2>Titre</h2>
  <p>Contenu de la carte</p>
</GlassCard>

// Avec variants
<GlassCard glow>Carte avec effet glow</GlassCard>
<GlassCard gradient>Carte avec gradient teinté</GlassCard>
```

**Props:**
- `children`: React.ReactNode - Contenu
- `className?`: string - Classes CSS additionnelles
- `hover?`: boolean - Activer l'effet hover (défaut: true)
- `glow?`: boolean - Effet glow avec bordure gradient
- `gradient?`: boolean - Gradient teinté en arrière-plan
- `onClick?`: () => void - Handler de clic

### GlassButton
Bouton avec effet glassmorphism.

```tsx
import { GlassButton } from '@/core/shared/components';

<GlassButton variant="primary" size="large" icon={<Send />}>
  Envoyer
</GlassButton>
```

**Props:**
- `children`: React.ReactNode - Texte du bouton
- `onClick?`: () => void - Handler de clic
- `variant?`: 'primary' | 'secondary' | 'danger' | 'brand' - Style du bouton
- `size?`: 'small' | 'medium' | 'large' - Taille
- `disabled?`: boolean - État désactivé
- `type?`: 'button' | 'submit' | 'reset' - Type HTML
- `icon?`: React.ReactNode - Icône

### GlassInput
Champ de saisie avec effet glassmorphism.

```tsx
import { GlassInput } from '@/core/shared/components';

<GlassInput
  value={email}
  onChange={setEmail}
  label="Email"
  placeholder="votre@email.com"
  type="email"
  required
  error={errorMessage}
/>
```

**Props:**
- `value`: string - Valeur
- `onChange`: (value: string) => void - Handler de changement
- `placeholder?`: string - Texte placeholder
- `type?`: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'
- `disabled?`: boolean - État désactivé
- `label?`: string - Label
- `error?`: string - Message d'erreur
- `required?`: boolean - Champ requis

### SearchBox
Barre de recherche glassmorphism.

```tsx
import { SearchBox } from '@/core/shared/components';

<SearchBox
  value={search}
  onChange={setSearch}
  placeholder="Rechercher..."
/>
```

### Toast
Notification glassmorphism.

```tsx
import { Toast } from '@/core/shared/components';

<Toast
  message="Données enregistrées"
  type="success"
  duration={3000}
  onClose={() => setToast(null)}
/>
```

**Types:** 'success' | 'error' | 'warning' | 'info'

### Alert
Alerte glassmorphism.

```tsx
import { Alert } from '@/core/shared/components';

<Alert type="success" title="Succès">
  Votre action a été effectuée avec succès.
</Alert>
```

### Toggle
Switch glassmorphism.

```tsx
import { Toggle } from '@/core/shared/components';

<Toggle
  checked={enabled}
  onChange={setEnabled}
  label="Activer la fonctionnalité"
/>
```

### Tag
Pill/Tag glassmorphism.

```tsx
import { Tag } from '@/core/shared/components';

<Tag>Validé</Tag>
<Tag onClick={() => handleClick()}>En attente</Tag>
```

### Tabs
Onglets glassmorphism.

```tsx
import { Tabs } from '@/core/shared/components';

const tabs = [
  { id: 'home', label: 'Accueil', icon: <Home /> },
  { id: 'settings', label: 'Paramètres', icon: <Settings /> }
];

<Tabs
  tabs={tabs}
  activeTab={activeTab}
  onChange={setActiveTab}
/>
```

### ProgressBar
Barre de progression glassmorphism.

```tsx
import { ProgressBar } from '@/core/shared/components';

<ProgressBar
  value={65}
  max={100}
  animated
  showLabel
/>
```

### Spinner
Indicateur de chargement glassmorphism.

```tsx
import { Spinner } from '@/core/shared/components';

<Spinner size="large" label="Chargement..." />
```

### Skeleton
Loader de skeleton glassmorphism.

```tsx
import { Skeleton } from '@/core/shared/components';

<Skeleton variant="card" />
<Skeleton variant="line" width="60%" />
<Skeleton variant="circle" />
```

### Stepper
Indicateur d'étapes glassmorphism.

```tsx
import { Stepper } from '@/core/shared/components';

const steps = [
  { id: '1', label: 'Informations' },
  { id: '2', label: 'Configuration' },
  { id: '3', label: 'Validation' }
];

<Stepper steps={steps} currentStep={1} />
```

### Modal
Modale glassmorphism.

```tsx
import { Modal } from '@/core/shared/components';

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Titre du modal"
  size="large"
>
  <p>Contenu du modal</p>
</Modal>
```

## 🎨 Classes CSS Utilitaires

### Surfaces en verre
```css
.glass-surface       /* Surface glassmorphism de base */
.blur-background     /* Effet de flou d'arrière-plan */
.gradient-tinted     /* Gradient teinté avec glassmorphism */
```

### Texte
```css
.text-gradient       /* Texte avec gradient Almadia */
```

### Effets
```css
.card-glow          /* Carte avec effet glow */
.brand-button       /* Bouton avec effet de brillance */
```

## 📐 Variables CSS

Toutes les variables sont définies dans `App.css`:

```css
:root {
  /* Couleurs */
  --primary-color: rgb(0, 89, 96);
  --accent-color: rgb(255, 199, 59);
  
  /* Glassmorphism */
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-border: rgba(255, 255, 255, 0.3);
  
  /* Shadows */
  --shadow: 0 8px 32px rgba(0, 89, 96, 0.1);
  --shadow-hover: 0 20px 60px rgba(0, 89, 96, 0.15);
  
  /* Border Radius */
  --border-radius-sm: 12px;
  --border-radius-md: 16px;
  --border-radius-lg: 20px;
  --border-radius-xl: 24px;
  --border-radius-xxl: 28px;
}
```

## 🎯 Caractéristiques

- **Backdrop Blur**: `blur(20px)` + `saturate(180%)` pour effet verre moderne
- **Animations Fluides**: GPU-accelerated avec transform et opacity
- **Border Radius**: 16-24px pour formes arrondies harmonieuses
- **Responsive**: Adapté à tous les écrans
- **Accessibilité**: Focus states et keyboard navigation

## 🚀 Utilisation

1. **Importer les composants**:
```tsx
import { GlassCard, GlassButton, Alert } from '@/core/shared/components';
```

2. **Utiliser les composants**:
```tsx
<GlassCard>
  <h2>Mon Composant</h2>
  <GlassButton variant="primary">Action</GlassButton>
</GlassCard>
```

3. **Utiliser les classes CSS**:
```tsx
<h1 className="text-gradient">Titre avec gradient</h1>
<div className="gradient-tinted">Contenu avec gradient teinté</div>
```

## 📱 Responsive

Le design system est entièrement responsive avec des breakpoints:
- Desktop: > 768px
- Tablet: 576px - 768px
- Mobile: < 576px

## 🎨 Best Practices

1. Utiliser les composants préfabriqués autant que possible
2. Respecter la palette de couleurs Almadia
3. Utiliser les variables CSS pour la cohérence
4. Préférer les gradients subtils pour les backgrounds
5. Maintenir le glassmorphism pour une esthétique unifiée

## 📄 Licence

Design System Reception © 2024 Almadia Solutions
