## Architecture et Technologies

Le projet repose sur une architecture modulaire combinant rapidité d'exécution, flexibilité métier et réactivité sur le terrain :

* **Backend (Python & Rust) :**
  * **Python :** Utilisé pour la logique métier principale, la gestion des API REST, l'administration et l'agrégation des données centralisées.
  * **Rust :** Utilisé pour les composants critiques nécessitant de hautes performances, la sécurité mémoire, la gestion de la concurrence ou le traitement rapide de flux de données (ex. synchronisation hors-ligne ou validation cryptographique).
* **Frontend (React) :**
  * **React :** Utilisé pour concevoir une interface utilisateur réactive, fluide et adaptée aux terminaux mobiles ou tablettes utilisés par les agents sur le terrain, incluant la gestion du cache local pour le mode hors-ligne.

---

## Prérequis et Installation

Assurez-vous de disposer des outils suivants sur votre machine avant de lancer le projet en local :

### 1. Prérequis système
* **Git** (pour le clonage et la gestion des versions)
* **Backend Python :** Python `3.12+` (recommandé : `3.14` ou `3.15`) et `pip` (ou `poetry` / `uv`)
* **Backend Rust :** Rust `1.85+` (édition 2024, dernière stable `1.100`) et `Cargo` (installables via `rustup`)
* **Frontend React :** Node.js `20 LTS` ou `22+` avec `npm`, `yarn` ou `pnpm` (compatible React `19+`)
* **Base de données :** PostgreSQL `15+` (ou SQLite pour les tests locaux)

### 2. Installation rapide

**Cloner le dépôt :**
```bash
git clone [https://github.com/votre-utilisateur/controle-routier.git](https://github.com/votre-utilisateur/controle-routier.git)
cd controle-routier
