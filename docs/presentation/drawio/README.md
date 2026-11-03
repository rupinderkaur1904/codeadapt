# UML diagrams (draw.io)

`CodeAdapt-UML.drawio` holds all ten diagrams from the presentation, one per page: four use
case diagrams, the class diagram and five sequence diagrams. Open it at
https://app.diagrams.net (File → Open from → Device) or in the draw.io desktop app, edit it
there, and export each page as PNG (File → Export as → PNG, zoom 200%).

The slides show PNG copies of these pages: `web/src/presentation/drawio/*.png`. After editing
a diagram, export the page and replace the matching PNG.

The first version was generated from the diagram data in `web/src/presentation/diagrams.tsx`:

    npx esbuild web/src/presentation/diagrams.tsx --bundle --format=cjs --platform=node --outfile=diagrams.cjs
    node -e "require('fs').writeFileSync('specs.json', JSON.stringify(require('./diagrams.cjs')))"
    node gen.cjs CodeAdapt-UML.drawio

`render.cjs` and `render.html` draw the pages with mxGraph (the library draw.io is built on;
`npm pack mxgraph@4.2.2` and unpack it into `mx/`) in a headless browser. Once you have edited
the .drawio file by hand, export from draw.io instead of regenerating, or your edits are lost.
