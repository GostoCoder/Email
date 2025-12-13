#!/bin/bash

# Script de démarrage pour l'architecture MVVM

echo "🚀 Démarrage de l'Outil Emailing (Architecture MVVM)"
echo "=================================================="
echo ""

# Vérifier si le venv existe
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer le venv
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install -r app/requirements.txt

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Attention: Fichier .env manquant"
    echo "💡 Créez un fichier .env avec vos paramètres SMTP"
    echo ""
fi

# Démarrer l'application
echo ""
echo "🌐 Démarrage de l'API sur http://localhost:5000"
echo "=================================================="
echo ""

python app/main.py
