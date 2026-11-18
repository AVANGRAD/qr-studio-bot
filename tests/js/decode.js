const fs = require('fs');
const { PNG } = require('pngjs');
const jsQR = require('jsqr');
const file = process.argv[2];
const png = PNG.sync.read(fs.readFileSync(file));
const result = jsQR(new Uint8ClampedArray(png.data), png.width, png.height);
if (!result) { console.log(JSON.stringify({ok:false})); process.exit(0); }
console.log(JSON.stringify({ok:true, data:result.data, version: result.version, location: result.location}));
