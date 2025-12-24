// ****************************************************
// Part-3: Estimasi Total Biomassa dengan Masking Vegetasi WorldCover dan Trend Biomassa
// ****************************************************
// Import assets
var exportPath = 'projects/ee-sorayatriutami/assets/agb/';
var startYear = 2021;
var endYear = 2023;

Map.centerObject(geometry);

// Definisi parameter visualisasi
var gediVis = {
  min: 0,
  max: 300,
  palette: ['#edf8fb','#b2e2e2','#66c2a4','#2ca25f','#006d2c'],
  bands: ['agbd']
};

// Load WorldCover untuk masking vegetasi
var worldcover = ee.ImageCollection('ESA/WorldCover/v200').first();
var gridScale = 100;
var gridProjection = ee.Projection('EPSG:32749').atScale(gridScale);

// Resample worldcover ke grid yang sama
var worldcoverResampled = worldcover
  .reduceResolution({
    reducer: ee.Reducer.mode(),
    maxPixels: 1024
  })
  .reproject({
    crs: gridProjection
});

// Buat mask vegetasi
var landCoverMask = worldcoverResampled.eq(10)  // Forest
    .or(worldcoverResampled.eq(20))            // Shrubland
    .or(worldcoverResampled.eq(30))            // Grassland
    .or(worldcoverResampled.eq(40))            // Cropland
    .or(worldcoverResampled.eq(95));           // Mangroves

// Array untuk menyimpan total AGB tahunan
var yearlyAGB = [];
var yearlyAGBDiff = [];

// Loop tahun untuk analisis perubahan
for (var year = startYear; year <= endYear; year++) {
  var yearString = String(year);
  
  // Load predicted AGB image
  var predictedImage;
  try {
    predictedImage = ee.Image(exportPath + 'predicted_agb_' + yearString);
  } catch (error) {
    print('Tidak ada data prediksi untuk tahun ' + yearString);
    continue;
  }
  
  // Mask vegetasi
  var predictedImageMasked = predictedImage.updateMask(landCoverMask);
  
  // Visualisasi
  Map.addLayer(predictedImageMasked, gediVis, 'AGB Masked ' + yearString, false);
  
  // Set tahun terakhir untuk ditampilkan
  if (year === endYear) {
    // Aktifkan layer tahun terakhir
    Map.layers().get(Map.layers().length() - 1).setShown(true); // predicted agb tahun terakhir
  }

     // Export hasil prediksi
    Export.image.toAsset({
      image: predictedImageMasked,
      description: 'AGB_' + yearString,
      assetId: exportPath + 'agb_' + yearString,
      region: geometry,
      crs: 'EPSG:32749',
      scale: gridScale,
      maxPixels: 1e10
    });
  
  // Hitung total AGB
  var pixelAreaHa = ee.Image.pixelArea().divide(10000);
  var predictedAgb = predictedImageMasked.multiply(pixelAreaHa);
  
  
  var stats = predictedAgb.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    scale: gridScale,
    maxPixels: 1e10,
    tileScale: 8,
    crs: 'EPSG:32749'
  });
  
  var totalAgb = stats.getNumber('agbd');
  yearlyAGB.push({year: year, agb: totalAgb});
  
  var validPixelMask = predictedImageMasked.gt(0);
  var validAreaImage = validPixelMask.multiply(pixelAreaHa).rename('area');
  var areaStats = validAreaImage.reduceRegion({
  reducer: ee.Reducer.sum(),
  geometry: geometry,
  scale: gridScale,
  maxPixels: 1e10,
  tileScale: 8,
  crs: 'EPSG:32749'
  });
  
  // 5. Get dengan default value untuk handle missing key
  var totalAreaHa = ee.Number(areaStats.get('area', 0));
  
  // Hitung perubahan AGB
  if (year > startYear) {
    var previousYearIndex = year - startYear - 1;
    if (previousYearIndex >= 0 && yearlyAGB.length > previousYearIndex) {
      var previousAgb = yearlyAGB[previousYearIndex].agb;
      var agbChange = totalAgb.subtract(previousAgb);
      var agbChangePercent = agbChange.divide(previousAgb).multiply(100);
      
      yearlyAGBDiff.push({
        year: year, 
        change: agbChange,
        changePercent: agbChangePercent
      });
      
      print('Perubahan AGB ' + (year-1) + ' ke ' + year + ': ' + 
            agbChange.getInfo() + ' Ton (' + 
            agbChangePercent.getInfo() + '%)');
    }
  }
  
  print('Total AGB ' + yearString + ': ' + totalAgb.getInfo() + ' Ton');
  
  if (year === endYear) { //luas area vegetasi setiap tahun sama
    // print luas area vegetasi
    print('=== LUAS AREA VEGETASI ' + ' ===', totalAreaHa);
  }
}
  
// hitung luas area setelah di masked
// 1. Buat pixelArea image
var pixelAreaImage = ee.Image.pixelArea();

// 2. Buat mask untuk pixel valid
var validPixelMask = predictedImage.gt(0);

// 3. Multiply area dengan mask - PENTING: rename band ke 'area'
var validAreaImage = validPixelMask.multiply(pixelAreaImage).rename('area');

// 4. Reduce dengan error handling
var areaStats = validAreaImage.reduceRegion({
  reducer: ee.Reducer.sum(),
  geometry: geometry,
  scale: gridScale,
  maxPixels: 1e10,
  tileScale: 8,
  crs: 'EPSG:32749'
});

// 5. Get dengan default value untuk handle missing key
var totalAreaM2 = ee.Number(areaStats.get('area', 0));
var totalAreaHa = totalAreaM2.divide(10000);

// Print dengan error handling
// print('Area Stats Dictionary:', areaStats);
// print('Available Keys:', areaStats.keys());

print('=== LUAS AREA TOTAL ' + ' ===', totalAreaHa);

var exportAGB = ee.FeatureCollection(yearlyAGB.map(function(item) {
    return ee.Feature(null, {
      year: item.year,
      total_agb: item.agb
    });
  }));
  
// Add dummy geometry to yearlyAGB
exportAGB = exportAGB.map(function(feature) {
return feature.setGeometry(ee.Geometry.Point([0, 0]));
});

  Export.table.toAsset({
    collection: exportAGB,
    description: 'AGBP_per_year',
    assetId: exportPath + 'AGBP_per_year'
  });



// Buat chart perubahan AGB
var agbData = ee.FeatureCollection(yearlyAGB.map(function(item) {
  return ee.Feature(null, {
    year: item.year,
    agb: item.agb
  });
}));

var agb_years = agbData.map(function(feature) {
  return feature.set('year', ee.String(ee.Number(feature.get('year')).format('%d')));
});

// Buat FeatureCollection untuk ekspor perubahan AGB tahunan
var exportAGBDiff = ee.FeatureCollection(yearlyAGBDiff.map(function(item) {
  return ee.Feature(null, {
    year: item.year,
    change: item.change,
    change_percent: item.changePercent
  });
}));

// Add dummy geometry to ABGDiff
exportAGBDiff = exportAGBDiff.map(function(feature) {
return feature.setGeometry(ee.Geometry.Point([0, 0]));
});
    
// Export ke assets
Export.table.toAsset({
  collection: exportAGBDiff,
  description: 'AGBP_Diff_per_year',
  assetId: exportPath + 'AGBP_Diff_per_year'
});

var agbChart = ui.Chart.feature.byFeature({
  features: agb_years,
  xProperty: 'year',
  yProperties: ['agb']
}).setChartType('LineChart')
  .setOptions({
    title: 'Total Above-Ground Biomass 2021-2023',
    hAxis: {title: 'Tahun'},
    vAxis: {title: 'Total AGB (Ton)'},
    pointSize: 5,
    lineWidth: 2,
    colors: ['#00bcd4']
  });

print(agbChart);

// Analisis Trend AGB
// 1. Kumpulkan citra tahunan
var yearlyImages = [];
for (var year = startYear; year <= endYear; year++) {
  var image = ee.Image(exportPath + 'agb_' + year);
  yearlyImages.push(image);
}

// 2. Hitung trend
var agbFirst = ee.Image(yearlyImages[0]);
var agbLast = ee.Image(yearlyImages[yearlyImages.length-1]);

var agbTrend = agbLast.subtract(agbFirst).divide(yearlyImages.length);

// 3. Parameter visualisasi
var gediVis = {
  min: 0,
  max: 300,
  palette: ['#edf8fb','#b2e2e2','#66c2a4','#2ca25f','#006d2c'],
  bands: ['agbd']
};

var trendVis = {
  min: -20,
  max: 5,
  palette: ['#d73027', '#fc8d59', '#fee08b', '#d9ef8b', '#91cf60']
};

Map.addLayer(agbTrend, trendVis, 'AGB Trend (Ton/Ha/Tahun)',false);

// Export to Assets
Export.image.toAsset({
  image: agbTrend,
  description: 'AGB_Trend',
  assetId: exportPath + 'agb_trend',
  crs: 'EPSG:32749',
  region: geometry,
  scale: 30,
  maxPixels: 1e10
});

// Hitung nilai max and min dari trend layer
var trendStats = agbTrend.reduceRegion({
  reducer: ee.Reducer.minMax(),
  geometry: geometry,
  scale: 30,          
  maxPixels: 1e13
});

print('Trend AGB min/max (Ton/ha/year):', trendStats);

// Daftar tahun yang dianalisis
var years = [2021, 2022, 2023];

// Loop untuk cek statistik agb setiap tahun
years.forEach(function(year) {
  var agb = ee.Image(exportPath + 'agb_' + year);
  var stats = agb.reduceRegion({
    reducer: ee.Reducer.minMax()
      .combine(ee.Reducer.mean(), '', true)
      .combine(ee.Reducer.sum(), '', true),
    geometry: geometry,
    scale: 30,
    maxPixels: 1e13
  });
  print('Statistik AGB ' + year + ':', stats);
});
