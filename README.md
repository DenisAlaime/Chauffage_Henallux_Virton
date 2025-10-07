# Générateur d’horaires XML – Henallux

Ce script permet de générer un fichier **XML d’horaires** à partir du web service Henallux ou de fichiers de test (*mock*).  
Il regroupe les événements par salle et par jour, fusionne les créneaux de 10 minutes en cours complets, et écrit chaque `<tNBEvent>` sur **une seule ligne**.  

---

## 🚀 Utilisation

### Commande de base (API réelle)
```bash
python generateur_horaire.py --salles C:\Data\salles.ini --out C:\Data\Horaire_all.xml --api "https://simple-planning.henallux.be/api/getHoraireSalle" --include-empty-days --verbose
```

- `--salles` : chemin vers un fichier `.ini` contenant les locaux (exemple ci-dessous).  
- `--out` : fichier XML de sortie.  
- `--api` : URL de l’API (toujours `https://simple-planning.henallux.be/api/getHoraireSalle`).  
- `--include-empty-days` : ajoute les jours vides (toujours 7 jours).  
- `--verbose` : affiche la progression dans le terminal.  

---

### Exemple de fichier `salles.ini`
```ini
salle01=IV-E202
salle02=IV-E203
salle03=IV-E310
salle04=IV-E106-Auditoire
```

---

### Mode test (sans Internet)

#### Avec un fichier unique (mock)
```bash
python generateur_horaire.py --salles C:\Data\salles.ini --out C:\Data\Horaire_all.xml --mock "C:\Data\Donnée brute2.txt" --include-empty-days --no-filter-location --verbose
```
- `--mock` : fichier JSON de test (toujours le même pour toutes les salles).  
- `--no-filter-location` : affiche les événements même si la salle ne correspond pas exactement.  

#### Avec un dossier de mocks (un fichier par salle)
Place dans un dossier `mocks/` un fichier par salle :  
- `IV-E202.json`  
- `IV-E203.json`  
- …  

Puis lance :
```bash
python generateur_horaire.py --salles C:\Data\salles.ini --out C:\Data\Horaire_all.xml --mock-dir C:\Data\mocks --include-empty-days --verbose
```

---

## ⚙️ Options avancées

- `--shift-hours N` : décale toutes les heures de **N** (ex. `-2` par défaut).  
  - `--shift-hours -2` → retire 2 h (défaut).  
  - `--shift-hours 0` → pas de décalage.  
  - `--shift-hours 1` → ajoute 1 h.  

---

## 📄 Sortie XML

Le fichier généré suit cette structure :

```xml
<dataentry>
<MAIN.DayOfWeek index="0">
<dDate>20250925</dDate>
<tNBEvent index="0"><LOCATION>IV-E310</LOCATION><TimeSTART>0810</TimeSTART><TimeEND>1010</TimeEND><SUMMARY>English</SUMMARY></tNBEvent>
<tNBEvent index="1"><LOCATION>IV-E203</LOCATION><TimeSTART>1010</TimeSTART><TimeEND>1210</TimeEND><SUMMARY>Physique</SUMMARY></tNBEvent>
</MAIN.DayOfWeek>
...
</dataentry>
```

- Chaque `<MAIN.DayOfWeek>` correspond à une date.  
- `<dDate>` contient la date au format `YYYYMMDD`.  
- Chaque `<tNBEvent>` correspond à un cours (fusionné en bloc).  

---

## ✅ Points importants

- Le script regroupe automatiquement les créneaux de 10 minutes consécutifs en **un seul bloc** par cours.  
- Chaque `<tNBEvent>` est écrit sur **une seule ligne**.  
- L’API est appelée en **POST** avec `action=getHoraireSalle` et `codeSalle=<NomSalle>`.  
- Les horaires sont ajustés par défaut de **–2 h** (`--shift-hours`).

---

## 🆕 Nouveautés et améliorations (version actuelle)

- **Chemins relatifs** : plus besoin de chemins absolus (ex. `C:\...`). Le script peut être exécuté depuis n'importe quel dossier.  
- **Nettoyage des fins de lignes** : les caractères `CR` indésirables sont supprimés automatiquement.  
- **Option `--eol`** : permet de choisir le style des fins de lignes du fichier XML généré :  
  - `lf` (par défaut, style Unix/Linux/macOS, identique à `horaire2_original.xml`)  
  - `crlf` (style Windows)  

Exemple :
```bash
python generateur_horaire_v2.py --salles salles.ini --out Horaire_all.xml --eol crlf
```

👉 Ces améliorations garantissent la compatibilité entre systèmes et évitent les problèmes de fichiers avec des fins de lignes mélangées.
