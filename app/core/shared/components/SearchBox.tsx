/**
 * SearchBox - Barre de recherche glassmorphism
 * Utilise le design system Reception
 */

import React from 'react';
import { Search } from 'lucide-react';

interface SearchBoxProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export const SearchBox: React.FC<SearchBoxProps> = ({
  value,
  onChange,
  placeholder = 'Rechercher...',
  className = ''
}) => {
  return (
    <div className={`search-box ${className}`}>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      <span className="search-icon">
        <Search size={20} />
      </span>
    </div>
  );
};

export default SearchBox;
