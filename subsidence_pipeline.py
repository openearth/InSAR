import os
from snappy import GPF
from snappy import ProductIO
from snappy import HashMap
from snappy import jpy
from snappy import WKTReader
import subprocess
import glob
import shutil
import sys
import gc




def read(filename):
    return ProductIO.readProduct(filename)

def write(product, filename):
    ProductIO.writeProduct(product, filename, "BEAM-DIMAP")

def write_netcdf(product, filename):
    ProductIO.writeProduct(product, filename, 'NetCDF4-CF')

def topsar_split(product, IW):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put('subswath', IW)
    parameters.put('selectedPolarisations', 'VV')
    return GPF.createProduct("TOPSAR-Split", parameters, product)

def apply_orbit_file(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put("Orbit State Vectors", "Sentinel Precise (Auto Download)")
    parameters.put("Polynomial Degree", 3)
    return GPF.createProduct("Apply-Orbit-File", parameters, product)


def back_geocoding(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put("Digital Elevation Model", "SRTM 3Sec (Auto Download)")
    parameters.put("DEM Resampling Method", "BILINEAR_INTERPOLATION")
    parameters.put("Resampling Type", "BILINEAR_INTERPOLATION")
    parameters.put("Mask out areas with no elevation", True)
    parameters.put("Output Deramp and Demod Phase", True)
    return GPF.createProduct("Back-Geocoding", parameters, product)


def interferogram(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put("Subtract flat-earth phase", True)
    parameters.put("Degree of \"Flat Earth\" polynomial", 5)
    parameters.put("Number of \"Flat Earth\" estimation points", 501)
    parameters.put("Orbit interpolation degree", 3)
    parameters.put("Include coherence estimation", True)
    parameters.put("Square Pixel", True)
    parameters.put("Independent Window Sizes", False)
    # parameters.put("Coherence Azimuth Window Size", 2)
    parameters.put("Coherence Range Window Size", 10)
    return GPF.createProduct("Interferogram", parameters, product)

def topsar_deburst(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put("Polarisations", "VV")
    return GPF.createProduct("TOPSAR-Deburst", parameters, product)

def topophase_removal(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put("Orbit Interpolation Degree", 3)
    parameters.put("Digital Elevation Model", "SRTM 3Sec (Auto Download)")
    parameters.put("Tile Extension[%]", 100)
    parameters.put("Output topographic phase band", False)
    parameters.put("Output elevation band", False)
    return GPF.createProduct("TopoPhaseRemoval", parameters, product)

def multi_looking(product):
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put('grSquarePixel', True)
    parameters.put('nRgLooks', 3)
    # parameters.put('nAzLooks', 1)
    parameters.put('outputIntensity', False)
    # parameters.put('sourceBands', source)
    return GPF.createProduct("MultiLook", parameters, product)

def goldstein_phasefiltering(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put("Adaptive Filter Exponent in(0,1]:", 1.0)
    # parameters.put("FFT Size", 64)
    # parameters.put("Window Size", 3)
    parameters.put("Use coherence mask", False)
    parameters.put("Coherence Threshold in[0,1]:", 0.2)
    return GPF.createProduct("GoldsteinPhaseFiltering", parameters, product)

def create_subset(product, wkt):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    """obtain polygon with VERTEX"""

    geom = WKTReader().read(wkt)
    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geom)
    return GPF.createProduct('Subset', parameters, product)

def unwrap_snaphu(product, temp_path):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters_snaphu = HashMap()
    parameters_snaphu.put("targetFolder", str(temp_path))
    # parameters_snaphu.put('Number of Tile Rows', 5)
    # parameters_snaphu.put('Number of Tile Columns', 5)
    parameters_snaphu.put('Number of Processors', 4)
    result_SNE = GPF.createProduct("SnaphuExport", parameters_snaphu, product)
    ProductIO.writeProduct(result_SNE, temp_path, "Snaphu")
    infile = os.path.join(temp_path, "snaphu.conf")
    with open(str(infile)) as lines:
        line = lines.readlines()[6]
        snaphu_string = line[1:].strip()
        snaphu_args = snaphu_string.split()
    process = subprocess.Popen(snaphu_args, cwd=str(temp_path))
    process.communicate()
    process.wait()
    print('done')


    unwrapped_list = glob.glob(str(temp_path) + "/UnwPhase*.hdr")
    unwrapped_hdr = str(unwrapped_list[0])
    unwrapped_read = ProductIO.readProduct(unwrapped_hdr)
    fn = os.path.join(temp_path, "unwrapped_read.dim")

    ProductIO.writeProduct(unwrapped_read, fn, "BEAM-DIMAP")
    unwrapped = ProductIO.readProduct(fn)

    snaphu_files = jpy.array('org.esa.snap.core.datamodel.Product', 2)
    snaphu_files[0] = product
    snaphu_files[1] = unwrapped
    result_SI = GPF.createProduct("SnaphuImport", parameters, snaphu_files)
    return result_SI

def PhaseToDisplacement(product):
    parameters = HashMap()
    result_PD = GPF.createProduct("PhaseToDisplacement", parameters, product)
    return result_PD

### TERRAIN CORRECTION
def terrain_correction(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put('demResamplingMethod', 'BILINEAR_INTERPOLATION') #alternatively use 'NEAREST_NEIGHBOUR'
    parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('demName', 'SRTM 3Sec')
    # parameters.put('pixelSpacingInMeter', 15.0)
    parameters.put('sourceBands', 'displacement')
    parameters.put('saveLocalIncidenceAngle', True)
    parameters.put('saveLatLon', True)
    # parameters.put('incidenceAngle', 'Use local incidence angle from Ellipsoid')
    return GPF.createProduct("Terrain-Correction", parameters, product)

def bandMathsProduct(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    BandDescriptor = jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
    targetBand = BandDescriptor()
    targetBand.name = 'displacement_vertical'
    targetBand.type = 'float32'
    targetBand.expression = 'displacement_VV * cos(localIncidenceAngle)'
    targetBands = jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    targetBands[0] = targetBand
    parameters.put('targetBands', targetBands)
    return GPF.createProduct('BandMaths', parameters, product)
def merge(product1, product2):
    sourceProducts = HashMap()
    sourceProducts.put('masterProduct', product1)
    sourceProducts.put('slaveProduct', product2)
    parameters = HashMap()
    return GPF.createProduct('Merge', parameters, sourceProducts)

def insar_pipeline(filename_1, filename_2):

    print('Reading SAR data')
    product_1 = read(filename_1)
    product_2 = read(filename_2)

    print('TOPSAR-Split')

    product_TOPSAR_1 = topsar_split(product_1, 'IW1')
    product_TOPSAR_2 = topsar_split(product_2, 'IW1')

    print('Applying precise orbit files')
    product_orbitFile_1 = apply_orbit_file(product_TOPSAR_1)
    product_orbitFile_2 = apply_orbit_file(product_TOPSAR_2)

    print('back geocoding')
    backGeocoding = back_geocoding([product_orbitFile_1, product_orbitFile_2])

    print('inerferogram generation')
    interferogram_formation = interferogram(backGeocoding)

    print('TOPSAR_deburst')
    TOPSAR_deburst = topsar_deburst(interferogram_formation)

    print('TopoPhase removal')
    TOPO_phase_removal =topophase_removal(TOPSAR_deburst)

    print('Multi-looking')
    MultiLook = multi_looking(TOPO_phase_removal)

    print('Goldstein filtering')
    Goldstein_phasefiltering = goldstein_phasefiltering(MultiLook)

    print('Create subset')
    # poly = "POLYGON((-44.1941 -20.3335,-43.9049 -20.3335,-43.9049 -20.0225,-44.1941 -20.0225,-44.1941 -20.3335))"
    poly = "POLYGON((-44.1417 -20.1408,-44.1 -20.1408,-44.1 -20.1066,-44.1417 -20.1066,-44.1417 -20.1408))"
    Subset = create_subset(Goldstein_phasefiltering, poly)

    print('Snaphu unwrapping')
    outputPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    snaphuPath = os.path.join(outputPath, 'snaphu')

    # Displacement = unwrap_snaphu_Displacement(Subset, snaphuPath)
    print('Unwrap with Snaphu and import to SNAP')
    unwrappedProduct = unwrap_snaphu(Subset, snaphuPath)

    print('Calculate displacement from unwrapped phase')
    displacementProduct = PhaseToDisplacement(unwrappedProduct)

    print('Perform terrain correction')
    terrainCorrected = terrain_correction(displacementProduct)

    # print('Calculate vertical displacement')
    #
    # verticalDisplacement = bandMathsProduct(terrainCorrected)
    #
    # print('merging')
    # mergedProduct = merge(verticalDisplacement, terrainCorrected)
    #
    # print('Write result to NetCDF4-CF file')
    # write_netcdf(terrainCorrected, os.path.join(outputPath, fileOut))
    print('Write result to BEAM-DIMAP')
    write(terrainCorrected, os.path.join(outputPath, fileOut))
    # # write(mergedProduct, os.path.join(outputPath, fileOut))
    # print('Done writing results')

    terrainCorrected.dispose()
    displacementProduct.dispose()
    unwrappedProduct.dispose()
    Subset.dispose()
    Goldstein_phasefiltering.dispose()
    TOPO_phase_removal.dispose()
    TOPSAR_deburst.dispose()
    product_orbitFile_1.dispose()
    product_orbitFile_2.dispose()
    product_1.dispose()
    product_2.dispose()

    print('Delete snaphu output')
    shutil.rmtree(snaphuPath)


path2input = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'input'))
infile_list = os.listdir(path2input)
infile_list = [f for f in infile_list if f.endswith('.zip')]
print(infile_list)

"""iterate through input files in pairs of two in order to create a time series"""
for master, slave in zip(infile_list, infile_list[1:]):
    print('master, slave: ', master, slave)
    fn1 = os.path.join(path2input, master)
    fn2 = os.path.join(path2input, slave)
    date_start = master.split('_')[6]
    date_end = slave.split('_')[6]
    fileOut = 'Displacement_LOS_%s_%s' % (date_start, date_end)
    insar_pipeline(fn1, fn2)
    gc.collect()



### USEFUL LINKS
"""SAR data (fn1 and fn2) were downloaded from https://search.asf.alaska.edu/#/
    options used on VERTEX site: File Types: SLC Beam Modes: IW Polarizations: VV+VH Flight Dir: Ascending Dataset: SA"""
"""https://forum.step.esa.int/t/slower-snappy-processing/6354/5"""
"""https://senbox.atlassian.net/wiki/spaces/SNAP/pages/19300362/How+to+use+the+SNAP+API+from+Python"""
"""https://gist.github.com/braunfuss/41caab61817fbae71a25bba82a02a8c0"""
"""https://forum.step.esa.int/t/snappy-sarsim-terrain-correction-runtimeerror-java-lang-nullpointerexception/8804"""
