# Contrôle Routier - Projet Open Source

[voir les outils](outils.md)

## À propos du projet

Ce dépôt héberge le code source d'une application open source dédiée à la modernisation du contrôle routier. Conçue pour être utilisée par les agents de sécurité et les autorités compétentes, cette solution vise à remplacer les méthodes de travail obsolètes par des outils numériques efficaces, rapides et fiables.

## Le constat : Un retard technologique majeur au Mali

Au Mali, le secteur du contrôle routier fait face à un défi de taille : un retard technologique critique.

Aujourd'hui, une grande partie des contrôles routiers sur le territoire national s'effectue encore de manière exclusivement manuelle :
* **Processus fastidieux :** Les agents utilisent des carnets papier pour noter les infractions, ce qui entraîne des pertes de temps considérables et des files d'attente interminables.
* **Manque de centralisation :** Les données recueillies sur le terrain ne sont pas centralisées. Il est donc extrêmement difficile pour l'État de faire des statistiques fiables sur les accidents, les infractions récurrentes ou l'état du parc automobile.
* **Risques d'erreurs et de fraudes :** La saisie manuelle augmente le risque d'erreurs humaines et rend plus complexe la traçabilité des amendes ou des documents vérifiés.
* **Lenteur des vérifications :** Vérifier l'assurance, la visite technique ou le permis de conduire d'un usager prend un temps anormalement long sans base de données interconnectée.

Face à la croissance du trafic routier et aux enjeux de sécurité, le maintien de ces méthodes archaïques n'est plus viable. La digitalisation du secteur routier n'est plus une option, mais une nécessité absolue.

## Notre solution

Ce projet open source est né de la volonté de combler ce fossé technologique. Il propose une application légère et intuitive qui permet aux agents sur le terrain de digitaliser l'ensemble du processus de contrôle, d'accélérer les interventions et de faciliter la remontée d'informations vers une base de données centrale pour les autorités.

En rendant ce projet open source, notre objectif est de permettre à la communauté de développeurs maliens et internationaux, aux ingénieurs de l'État et aux acteurs de la sécurité routière de collaborer. Ensemble, nous pouvons construire une technologie adaptée aux réalités du terrain, transparente et souveraine.

## Objectifs du projet

1. Moderniser les opérations de contrôle routier au Mali.
2. Réduire le temps d'intervention des agents sur le terrain.
3. Garantir l'application exacte et transparente du règlement tarifaire.
4. Fournir des données statistiques fiables à l'État pour une meilleure politique de sécurité routière.
5. Créer une communauté de contributeurs autour de la GovTech (technologie d'État) en Afrique de l'Ouest.

## Fonctionnalités clés

L'application couvre l'ensemble du cycle de contrôle et de verbalisation sur le terrain :

* **Identification automatique des plaques (ANPR / OCR) :** Lecture et reconnaissance optique des plaques d'immatriculation via la caméra du terminal ou par saisie assistée.
* **Identification des véhicules et propriétaires :** Interrogation sécurisée des fichiers d'immatriculation pour vérifier l'identité du propriétaire, le statut administratif du véhicule, l'assurance et la visite technique.
* **Détection et qualification des infractions :** Assistance à la détection des anomalies (défaut de pièces, excès de vitesse, surcharge, non-respect du code de la route) et sélection rapide des infractions constatées.
* **Calcul automatique selon le règlement tarifaire :** Application dynamique des montants d'amendes en fonction de la grille tarifaire officielle en vigueur, de la catégorie du véhicule et d'éventuelles circonstances aggravantes ou récidives.
* **Génération de contraventions numériques :** Édition instantanée du procès-verbal électronique avec identifiant unique, horodatage, géolocalisation et génération d'un reçu (format numérique ou impression thermique).
* **Mode hors-ligne et synchronisation :** Sauvegarde locale chiffrée des contrôles et contraventions dans les zones sans couverture réseau, avec synchronisation automatique vers le serveur central dès le retour de la connexion.

## Architecture et Technologies

La répartition des responsabilités entre les langages tire parti des forces de chaque écosystème :

* **Backend (Python & Rust) :**
  * **Python :** Gestion de la logique métier, administration de la grille tarifaire officielle, API REST, interconnexion avec les bases de données nationales (immatriculations, assurances) et génération des documents officiels (PDF/reçus).
  * **Rust :** Traitement haute performance des images et reconnaissance optique des plaques d'immatriculation (OCR/ANPR), moteur d'évaluation rapide des règles d'infraction, chiffrement des données locales et gestion de la synchronisation hors-ligne.
* **Frontend (React) :**
  * **React :** Interface terrain ergonomique et réactive pour les agents, capture vidéo/photo pour le scan des plaques, consultation instantanée des fiches véhicules et gestion du stockage local persistant.

## Prérequis et Installation

Assurez-vous de disposer des outils suivants sur votre machine avant de lancer le projet en local :

### 1. Prérequis système

* **Git** (pour le clonage et la gestion des versions)
* **Backend Python :** Python `3.12+` et `pip` (ou `poetry` / `uv`)
* **Backend Rust :** Rust `1.85+` (édition 2024) et `Cargo` (installables via `rustup`)
* **Frontend React :** Node.js `20 LTS` ou `22+` avec `npm`, `yarn` ou `pnpm`
* **Base de données :** SQLite + SpatiaLite en développement ; PostgreSQL `15+` + PostGIS en production

### 2. Installation rapide

**Cloner le dépôt :**
```bash
git clone https://github.com/Bah-traore/systeme-controle-routier.git
cd systeme-controle-routier
```

**Configurer le Backend (Python) :**
```bash
cd backend/py-thon
python -m venv venv
source venv/bin/activate  # Sous Windows : venv\Scripts\activate
pip install -r ../../requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
python -c "from secrets import token_urlsafe; print(token_urlsafe(64))"
```

Remplacez `SECRET_KEY` dans `.env` par la clé générée. SQLite est configuré par défaut avec SpatiaLite pour les zones géographiques ; installez la bibliothèque système `mod_spatialite` (paquet `libsqlite3-mod-spatialite` sur Debian/Ubuntu). Redis doit également être disponible pour le cache, les sessions, les tâches Celery et Channels configurés dans `.env`.

En production, sélectionnez `config.settings.prod`, fournissez une `DATABASE_URL` PostgreSQL/PostGIS, une `SECRET_KEY` aléatoire, les vrais domaines dans `ALLOWED_HOSTS` et `CORS_ALLOWED_ORIGINS`, puis activez `SECURE_SSL_REDIRECT=True`. Les réglages de production refusent les origines localhost et une redirection HTTPS désactivée.

**Compiler les modules Rust :**
```bash
cd ../rust
cargo build --release
```

**Configurer le Frontend (React) :**
```bash
cd ../../frontend
npm install
npm run dev
```

## Comment contribuer ?

Le projet est ouvert à tous. Que vous soyez développeur, designer, expert en sécurité routière ou simplement citoyen intéressé, votre aide est la bienvenue.

1. Forkez le projet.
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/NouvelleFonctionnalite`).
3. Commitez vos changements (`git commit -m 'Ajout d'une nouvelle fonctionnalité'`).
4. Pushez vers la branche (`git push origin feature/NouvelleFonctionnalite`).
5. Ouvrez une Pull Request.