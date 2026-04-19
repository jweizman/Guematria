# Guematria - Bible Hébraïque

Application Flask qui charge un chapitre de la Bible en hébreu via l'API Sefaria
et calcule la guematria (valeur numérique) de chaque mot au clic.

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python app.py
```

Puis ouvrir http://localhost:5000

## Utilisation

- Entrer une référence au format Sefaria (ex: `Genesis.1`, `Exodus.3`, `Psalms.23`)
- Cliquer "Charger"
- Cliquer sur n'importe quel mot hébreu pour voir sa guematria détaillée
  (lettre par lettre + total)

## Valeurs de guematria

Calcul standard (mispar hechrachi) : les lettres finales gardent la valeur
de leur forme normale (ך=20, ם=40, ן=50, ף=80, ץ=90). Les signes de
vocalisation (nikud) et de cantillation (teamim) sont ignorés.
