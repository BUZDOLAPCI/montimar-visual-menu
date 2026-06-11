# Montimar Mierlo Visual Menu

A practical English visual menu for Montimar Mierlo. It includes every listed menu entry from the public menu page, translated descriptions, prices, and one image per dish.

Source menu: https://www.montimar.nl/menukaart/

Photos are representative visual aids. Some come from Montimar's own public website where a matching image was available; the rest are representative external web or Wikimedia Commons images. Attribution and source details are in `data/photo_sources.json`.

## Local use

Open `index.html` in a browser, or serve the folder with:

```bash
python3 -m http.server 8000
```

## Regenerate

```bash
python3 scripts/build_visual_menu.py
```
