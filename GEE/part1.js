// ****************************************************
// Part-1: Preprocessing dan Persiapan Data Multi-Tahun
// ****************************************************

// Pilih region of interest
Map.centerObject(geometry);

// Pilih dataset
var gedi = ee.ImageCollection('LARSE/GEDI/GEDI04_A_002_MONTHLY');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED');
var glo30 = ee.ImageCollection('COPERNICUS/DEM/GLO30');

// Definisi periode waktu 3 tahun
var startYear = 2021;
var endYear = 2023;

// Preprocessing
var scaleBands = function(image) {
  return image.multiply(0.0001)
    .copyProperties(image, ['system:time_start']);
};

// Fungsi Cloud Score+ mask 
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
var csPlusBands = csPlus.first().bandNames();

function maskLowQA(image) {
  var qaBand = 'cs';
  var clearThreshold = 0.5;
  var mask = image.select(qaBand).gte(clearThreshold);
  return image.updateMask(mask);
}

// Perhitungan indeks vegetasi
var addIndices = function(image) {
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi');
  var mndwi = image.normalizedDifference(['B3', 'B11']).rename('mndwi'); 
  var ndbi = image.normalizedDifference(['B11', 'B8']).rename('ndbi');
  var evi = image.expression(
    '2.5 * ((NIR - RED)/(NIR + 6*RED - 7.5*BLUE + 1))', {
      'NIR': image.select('B8'),
      'RED': image.select('B4'),
      'BLUE': image.select('B2')
    }).rename('evi');
  var bsi = image.expression(
      '(( X + Y ) - (A + B)) /(( X + Y ) + (A + B)) ', {
        'X': image.select('B11'),
        'Y': image.select('B4'),
        'A': image.select('B8'),
        'B': image.select('B2'),
    }).rename('bsi');
  
  return image
    .addBands(ndvi)
    .addBands(mndwi)
    .addBands(ndbi)
    .addBands(evi)
    .addBands(bsi);
};

// Fungsi GEDI quality
var qualityMask = function(image) {
  return image.updateMask(image.select('l4_quality_flag').eq(1))
      .updateMask(image.select('degrade_flag').eq(0));
};

var errorMask = function(image) {
  var relative_se = image.select('agbd_se').divide(image.select('agbd'));
  return image.updateMask(relative_se.lte(0.5));
};

var agbMaxMask = function(image) {
  return image.updateMask(image.select('agbd').lt(650));
};

// Persiapan data DEM  (sama untuk semua tahun)
var glo30Filtered = glo30.filter(ee.Filter.bounds(geometry)).select('DEM');
// proyeksi DEM
var demProj = glo30Filtered.first().select(0).projection();
// Buat mosaik dari beberapa gambar dan set proyeksi
var elevation = glo30Filtered.mosaic().rename('dem').setDefaultProjection(demProj);
// perhitungan slope
var slope = ee.Terrain.slope(elevation).rename('slope');
// gabungkan slope dan elevation bands
var demBands = elevation.addBands(slope);

// Function untuk mask slope
var slopeMask = function(image) {
  return image.updateMask(slope.lt(30));
};

Map.addLayer(
  demBands.select('dem').clip(geometry),
  {min: -1, max: 10, palette: ['#543005', '#bf812d', '#f6e8c3', '#c7eae5', '#35978f', '#003c30']},
  'DEM (Elevasi)',
  false // Tampilkan secara default
);

Map.addLayer(
  demBands.select('slope').clip(geometry),
  {min: -1, max: 10, palette: ['#543005', '#bf812d', '#f6e8c3', '#c7eae5', '#35978f', '#003c30']},
  'Slope (Kemiringan)',
  false // Disembunyikan secara default, bisa diaktifkan manual
);

// Parameter visualisasi
var rgbVis = {
  min: 0.0, max: 0.3, gamma: 1.2,
  bands: ['B4', 'B3', 'B2'],
};

var gediVis = {
  min: 0,
  max: 200,
  palette: ['#edf8fb','#b2e2e2','#66c2a4','#2ca25f','#006d2c'],
  bands: ['agbd']
};

// Loop melalui semua tahun untuk memproses data dan visualisasi
for (var year = startYear; year <= endYear; year++) {
  var startDate = ee.Date.fromYMD(year, 1, 1);
  var endDate = startDate.advance(1, 'year');
  var yearString = String(year);
  
  // Process Sentinel-2 data
  var filteredS2 = s2
    .filter(ee.Filter.date(startDate, endDate))
    .filter(ee.Filter.bounds(geometry));
    
  var s2Projection = ee.Image(filteredS2.first()).select('B4').projection();
  
  var filteredS2WithCs = filteredS2.linkCollection(csPlus, csPlusBands);
  
  var s2Processed = filteredS2WithCs
    .map(maskLowQA)
    .select('B.*')
    .map(scaleBands)
    .map(addIndices);

  var s2Composite = s2Processed.median()
    .setDefaultProjection(s2Projection);
  
  // Process GEDI data
  var gediFiltered = gedi
    .filter(ee.Filter.date(startDate, endDate))
    .filter(ee.Filter.bounds(geometry));
  
  // Skip tahun jika tidak ada data GEDI (untuk validasi estimasi)
  if (gediFiltered.size().getInfo() === 0) {
    print('Tidak ada data GEDI untuk tahun ' + yearString);
    continue;
  }
  
  var gediProjection = ee.Image(gediFiltered.first()).select('agbd').projection();
  
  var gediProcessed = gediFiltered
  .map(qualityMask)
  .map(errorMask)
  .map(slopeMask)
  .map(agbMaxMask);
  
  var gediMosaic = gediProcessed.mosaic()
    .select('agbd').setDefaultProjection(gediProjection);
    
  // Pastikan gediFiltered sudah difilter sesuai tahun dan area
  var gediRawMosaic = gediFiltered
    .mosaic()
    .select('agbd')
    .setDefaultProjection(gediProjection);
  
  // Tampilkan layer GEDI L4A sebelum masking
  Map.addLayer(
    gediRawMosaic.clip(geometry),
    gediVis,
    'GEDI L4A RAW ' + yearString,
    false // Layer disembunyikan secara default, aktifkan manual jika perlu
  );

  // Sentinel-2 composite
  Map.addLayer(
    s2Composite.clip(geometry), 
    rgbVis, 
    'Sentinel-2 Composite ' + yearString,
    false  // Semua layer disembunyikan secara default kecuali tahun terakhir
  );
  
  // GEDI mosaic
  Map.addLayer(
    gediMosaic.clip(geometry), 
    gediVis, 
    'GEDI L4A Mosaic ' + yearString,
    false  // Semua layer disembunyikan secara default kecuali tahun terakhir
  );
  
  // Set tahun terakhir untuk ditampilkan
  if (year === endYear) {
    // Aktifkan layer tahun terakhir
    Map.layers().get(Map.layers().length() - 2).setShown(true); // S2 tahun terakhir
    Map.layers().get(Map.layers().length() - 1).setShown(true); // GEDI tahun terakhir
  }
  
  // Export yearly assets
  var exportPath = 'projects/ee-sorayatriutami/assets/agb/';
  Export.image.toAsset({
    image: s2Composite.clip(geometry),
    description: 'S2_Composite_' + yearString,
    assetId: exportPath + 's2_composite_' + yearString,
    region: geometry,
    scale: 10,
    maxPixels: 1e10
  });
  
  Export.image.toAsset({
    image: gediMosaic.clip(geometry),
    description: 'GEDI_Mosaic_' + yearString,
    assetId: exportPath + 'gedi_mosaic_' + yearString,
    region: geometry,
    scale: 25,
    maxPixels: 1e10
  });
}

// Export DEM bands sekali saja (tidak berubah per tahun)
Export.image.toAsset({
  image: demBands.clip(geometry),
  description: 'DEM_Bands',
  assetId: exportPath + 'dem_bands',
  crs: 'EPSG:32749',
  region: geometry,
  scale: 30,
  maxPixels: 1e10
});

// Tambahkan panel kontrol untuk memilih tahun
var yearSelector = ui.Select({
  items: [ '2021', '2022', '2023'],
  value: '2023',
  onChange: function(selected) {
    // Sembunyikan semua layer terlebih dahulu
    for (var i = 0; i < Map.layers().length(); i++) {
      var layer = Map.layers().get(i);
      var layerName = layer.getName();
      // Sembunyikan semua layer Sentinel dan GEDI
      if (layerName.indexOf('Sentinel-2') !== -1 || layerName.indexOf('GEDI') !== -1) {
        layer.setShown(false);
      }
    }
    
    // Tampilkan layer untuk tahun yang dipilih
    for (var i = 0; i < Map.layers().length(); i++) {
      var layer = Map.layers().get(i);
      var layerName = layer.getName();
      if (layerName.indexOf(selected) !== -1) {
        layer.setShown(true);
      }
    }
  }
});

var panel = ui.Panel({
  widgets: [
    ui.Label('Pilih Tahun untuk Visualisasi:'),
    yearSelector  
  ],
  style: {position: 'top-left'}
});

Map.add(panel);
