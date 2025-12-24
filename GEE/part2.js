// ****************************************************
// Part-2: Estimasi Biomassa dengan Random Forest Model
// ****************************************************

// Import assets dan definisi parameter
var exportPath = 'projects/ee-sorayatriutami/assets/agb/';
var startYear = 2021;
var endYear = 2023;
var demBands = ee.Image(exportPath + 'dem_bands');

// Definisi proyeksi dan skala
var gridScale = 100;
var gridProjection = ee.Projection('EPSG:32749').atScale(gridScale); //ikuti epsg utm lokal di kalimantan tengah (sama dgn sentinel,dem,gedi)

// Parameter visualisasi
var rgbVis = {
  min: 0.0, max: 0.3, gamma: 1.2,
  bands: ['B4', 'B3', 'B2'],
};
    

var gediVis = {
  min: 0, max: 300,
  palette: ['#edf8fb','#b2e2e2','#66c2a4','#2ca25f','#006d2c'],
  bands: ['agbd']
};

// Array untuk menyimpan hasil analisis
var modelsRMSE = [];
var yearlyFeatureImportance = {};

// Fungsi ekstraksi data training
var extractTrainingData = function(image) {
  var predicted = 'agbd';
  var classMask = image.select(predicted).mask().toInt().rename('class');
  return image.addBands(classMask)
    .stratifiedSample({
      numPoints: 1000,
      classBand: 'class',
      classValues: [0,1],
      classPoints: [0,1000],
      region: geometry,
      scale: gridScale,
      tileScale: 16
    });
};

// Panel untuk menampilkan model comparison
var modelPanel = ui.Panel({
  style: {
    position: 'top-right',
    padding: '8px'
  }
});
ui.root.add(modelPanel);

// Looping analisis tahunan
for (var year = startYear; year <= endYear; year++) {
  var yearString = String(year);
  
  // Coba load data
  try {
    var s2Composite = ee.Image(exportPath + 's2_composite_' + yearString);
    var gediMosaic = ee.Image(exportPath + 'gedi_mosaic_' + yearString);
    
    var geometry = s2Composite.geometry();
    Map.centerObject(geometry);
    
    // Extract predictors and predicted variable
    var s2Bands = s2Composite.bandNames();
    var demBandNames = demBands.bandNames();
    var predictors = s2Bands.cat(demBandNames);
    var predicted = gediMosaic.bandNames().get(0);
    
    print('Model Predictors: ', predictors);
    
    // Stack images dan resampling
    var stacked = s2Composite
      .addBands(demBands)
      .addBands(gediMosaic);
      
    var stacked = stacked.resample('bilinear');
    
    var stackedResampled = stacked
      .reduceResolution({
        reducer: ee.Reducer.mean(),
        maxPixels: 1024
      })
      .reproject({
        crs: gridProjection
    });
    
    var stackedResampled = stackedResampled.updateMask(stackedResampled.mask().gt(0));
      
    Map.addLayer(stackedResampled, rgbVis, 'S-2 (Resampled) ' + yearString, false);  
    Map.addLayer(stackedResampled, gediVis, 'GEDI L4A (Resampled) ' + yearString, false);
    
    // Extract training data
    var training = extractTrainingData(stackedResampled);
    
    // Train model
    var model = ee.Classifier.smileRandomForest(50)
      .setOutputMode('REGRESSION')
      .train({
        features: training,
        classProperty: predicted,
        inputProperties: predictors
    });
      
    print('Number of Training Features', training.size()) ; 
    print('Sample Training Features ' + yearString, training.first());
    
    // Evaluasi model
    var trained = training.classify({
      classifier: model,
      outputName: 'agbd_predicted'
    });
    
    // Hitung RMSE
    var calculateRmse = function(input) {
      var observed = ee.Array(input.aggregate_array('agbd'));
      var predicted = ee.Array(input.aggregate_array('agbd_predicted'));
      return observed.subtract(predicted).pow(2)
        .reduce('mean', [0]).sqrt().get([0]);
    };
    
    var rmse = calculateRmse(trained);
    modelsRMSE.push({year: year, rmse: rmse});
    print('RMSE', rmse)
    
    // Analisis Feature Importance
    var importance = ee.Dictionary(model.explain().get('importance'));
    var sumImportance = importance.values().reduce(ee.Reducer.sum());
    var importanceRelative = importance.map(function(key, value){
      return ee.Number(value).divide(sumImportance).multiply(100);
    });
    
    yearlyFeatureImportance[yearString] = importanceRelative;
    
    // Visualisasi feature importance
    var featureImportanceChart = ui.Chart.array.values({
      array: ee.Array(importanceRelative.values()),
      axis: 0,
      xLabels: importanceRelative.keys()
    }).setChartType('ColumnChart')
      .setOptions({
        width: 800,
        height: 400,
        title: 'Kepentingan Relatif Variabel (' + yearString + ')',
        hAxis: {title: 'Band', slantedText: true, slantedTextAngle: 45, textStyle: { fontSize: 12}},
        vAxis: {title: 'Kepentingan (%)'},
        legend: {position: 'none'},
        colors: ['#525252']
      });
    
    print(featureImportanceChart);
    
    // Prediksi untuk semua piksel
    var predictedImage = stackedResampled.classify({
      classifier: model,
      outputName: 'agbd'
    });
    
    // Buat grafik observed vs predicted
    var chart = ui.Chart.feature.byFeature({
      features: trained.select(['agbd', 'agbd_predicted']),
      xProperty: 'agbd',
      yProperties: ['agbd_predicted']
    }).setChartType('ScatterChart')
    .setOptions({
      title: 'Observed vs Predicted AGB Dencity (Ton/Ha) ' + yearString,
      dataOpacity: 0.8,
      hAxis: {'title': 'Observed (Ton/ha)'},
      vAxis: {'title': 'Predicted (Ton/ha)'},
      series: {
        0: {
          visibleInLegend: false,
          color: '#525252',
          pointSize: 3,
          pointShape: 'triangle',
        },
      },
      trendlines: {
        0: {
          type: 'linear', 
          color: 'black', 
          lineWidth: 1,
          visibleInLegend: true,
          showR2: true
        }
      },
      chartArea: {left: 100, bottom:100, width:'50%'},
    });
    
    print(chart);

    // Add dummy geometry to trained data
    trained = trained.map(function(feature) {
      return feature.setGeometry(ee.Geometry.Point([0, 0]));
    });

    // Export observed vs predicted AGB
    Export.table.toAsset({
      collection: trained.select(['agbd', 'agbd_predicted']),
      description: 'Observed_vs_Predicted_' + yearString,
      assetId: exportPath + 'Observed_vs_Predicted_' + yearString
    });
    
    // Export hasil prediksi
    Export.image.toAsset({
      image: predictedImage,
      description: 'Predicted_AGB_' + yearString,
      assetId: exportPath + 'predicted_agb_' + yearString,
      region: geometry,
      crs: 'EPSG:32749',
      scale: gridScale,
      maxPixels: 1e10
    });
    
    // Tampilkan hasil pada peta
    Map.addLayer(
      predictedImage, gediVis, 'Predicted AGB ' + yearString, false);
    
    // Tampilkan rmse model di panel
    modelPanel.add(ui.Label('Model ' + yearString + ' ✓ RMSE: ' + 
      ee.Number(rmse).round().getInfo() + ' Ton/ha'));
      
  } catch (error) {
    print('Tidak ada data untuk tahun ' + yearString + ': ' + error);
    modelPanel.add(ui.Label('Model ' + yearString + ' ✗ Data tidak tersedia'));
  }
}

// Visualisasi perbandingan RMSE antar tahun
if (modelsRMSE.length > 0) {
  var rmseData = ee.FeatureCollection(modelsRMSE.map(function(item) {
    return ee.Feature(null, {
      year: item.year,
      rmse: item.rmse
    });
  }));
  
  var years = rmseData.map(function(feature) {
  return feature.set('year', ee.String(ee.Number(feature.get('year')).format('%d')));
});
  
  var rmseChart = ui.Chart.feature.byFeature({
    features: years,
    xProperty: 'year',
    yProperties: ['rmse']
  }).setChartType('LineChart')
    .setOptions({
      title: 'Perbandingan RMSE Model 2021-2023',
      hAxis: {title: 'Tahun'},
      vAxis: {title: 'RMSE (Ton/ha)'},
      legend: {position: 'none'},
      colors: ['#ff5722'],
      pointSize: 5
    });
  
  print(rmseChart);
}
    // Add dummy geometry to rmseData
    rmseData = rmseData.map(function(feature) {
    return feature.setGeometry(ee.Geometry.Point([0, 0]));
    });
    
    // Export RMSE sebagai CSV
    Export.table.toAsset({
      collection: rmseData,
      description: 'RMSE_per_year',
      assetId: exportPath + 'RMSE_per_year',
    });
