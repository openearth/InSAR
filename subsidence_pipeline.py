import sys
# sys.path.append('/home/wilms/.snap/snap-python')
# sys.path.append('C:\\Users\\wilms\\.snap\\snap-python')
import os
from snappy import GPF
from snappy import ProductIO
from snappy import HashMap
from snappy import jpy
from snappy import WKTReader
import subprocess
import glob
import shutil
import gc
import time
import multiprocessing


def read(filename):
    return ProductIO.readProduct(filename)

def write(product, filename):
    ProductIO.writeProduct(product, filename, "BEAM-DIMAP")

def write_netcdf(product, filename):
    ProductIO.writeProduct(product, filename, 'NetCDF4-CF')
# def test(result_SNE):
#     # HashMap = jpy.get_type('java.util.HashMap')
#     # parameters = HashMap()
#     # parameters.put("targetFolder", '/mnt/d/PROJECTS/grace/SAR/output/snaphu')
#     # result_SNE = GPF.createProduct("SnaphuExport", parameters, Subset)
#     print('writing NOWWWW')
#     ProductIO.writeProduct(result_SNE, '/mnt/d/PROJECTS/grace/SAR/output/snaphu/', "Snaphu")
def test(b):
    ProductIO.writeProduct(b, '/mnt/d/PROJECTS/grace/SAR/output/snaphu/', "Snaphu")

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
    parameters.put("Digital Elevation Model", "SRTM 1Sec (Auto Download)")
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

def multi_looking(product): #"""not used for Faraz's work"""
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put('grSquarePixel', True)
    parameters.put('nRgLooks', 3)
    parameters.put('outputIntensity', False)
    return GPF.createProduct("MultiLook", parameters, product)

def goldstein_phasefiltering(product):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put("Adaptive Filter Exponent in(0,1]:", 1.0)
    parameters.put("FFT Size", 64)
    parameters.put("Window Size", 3)
    parameters.put("Use coherence mask", True)
    parameters.put("Coherence Threshold in[0,1]:", 0.3) #0.7 at least or 0.6 were used by SkyGeo...hmmm
    return GPF.createProduct("GoldsteinPhaseFiltering", parameters, product)

def create_subset(product, wkt):
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    """obtain polygon with VERTEX"""
    geom = WKTReader().read(wkt)
    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geom)
    return GPF.createProduct('Subset', parameters, product)

def export_snaphu(product, snaphu_dir):
    # Hashmap is used to provide access to all JAVA operators
    HashMap = jpy.get_type('java.util.HashMap')

    parameters = HashMap()
    parameters.put("targetFolder", snaphu_dir)
    parameters.put("statCostMode", "DEFO")
    parameters.put("initMethod", "MCF")
    parameters.put("numberOfTileRows", 5)
    parameters.put("numberOfTileCols", 5)
    parameters.put("numberOfProcessors", 4)
    parameters.put("rowOverlap", 200)
    parameters.put("colOverlap", 200)
    parameters.put("tileCostThreshold", 500)


    return GPF.createProduct("SnaphuExport", parameters, product)

def unwrap_snaphu(snaphu_dir):
    infile = os.path.join(snaphu_dir, "snaphu.conf")
    with open(str(infile)) as lines:
        line = lines.readlines()[6]
        snaphu_string = line[1:].strip()
        snaphu_args = snaphu_string.split()
    process = subprocess.Popen(snaphu_args, cwd=str(snaphu_dir))
    process.communicate()
    process.wait()
    print('done')

def import_snaphu(product, snaphu_dir):
    parameters = HashMap()
    unwrapped_list = glob.glob(str(snaphu_dir) + "/UnwPhase*.hdr")
    unwrapped = ProductIO.readProduct(str(unwrapped_list[0]))
    snaphu_files = jpy.array('org.esa.snap.core.datamodel.Product', 2)
    snaphu_files[0] = product
    snaphu_files[1] = unwrapped
    result_SI = GPF.createProduct("SnaphuImport", parameters, snaphu_files)
    return result_SI

def PhaseToDisplacement(product):
    parameters = HashMap()
    result_PD = GPF.createProduct("PhaseToDisplacement", parameters, product)
    return result_PD

def merge(product1, product2):
    sourceProducts = HashMap()
    sourceProducts.put('masterProduct', product1)
    sourceProducts.put('slaveProduct', product2)
    parameters = HashMap()
    return GPF.createProduct('Merge', parameters, sourceProducts)


def terrain_correction(product):
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put('demResamplingMethod', 'BILINEAR_INTERPOLATION') #alternatively use 'NEAREST_NEIGHBOUR' or cubic
    parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('demName', 'SRTM 3Sec')
    # parameters.put('pixelSpacingInMeter', 15.0)
    parameters.put('saveLocalIncidenceAngle', True)
    parameters.put('saveLatLon', True)
    return GPF.createProduct("Terrain-Correction", parameters, product)

def bandMathsProduct(product):
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    BandDescriptor = jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
    targetBand = BandDescriptor()
    bands = list(product.getBandNames())
    coh = [b for b in bands if b.startswith('coh')][0]
    targetBand.name = 'displacement_coh'
    targetBand.type = 'float32'
    targetBand.expression = 'IF %s <=0.3 THEN NaN ELSE displacement_VV' %coh
    targetBands = jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    targetBands[0] = targetBand
    parameters.put('targetBands', targetBands)
    return GPF.createProduct('BandMaths', parameters, product)

def bandMathsProduct2(product):
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



def insar_pipeline(filename_1, filename_2):

    print('Reading SAR data')
    product_1 = read(filename_1)
    product_2 = read(filename_2)

    print('TOPSAR-Split')

    product_TOPSAR_1 = topsar_split(product_1, 'IW2')
    product_TOPSAR_2 = topsar_split(product_2, 'IW2')

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

    ##removing multi-looking to increase resolution for comparison
    print('Multi-looking')
    MultiLook = multi_looking(TOPO_phase_removal)

    print('Goldstein filtering')
    Goldstein_phasefiltering = goldstein_phasefiltering(MultiLook)


    print('Create subset_0')
    # poly = "POLYGON((106.6896 -6.2759, 106.9204 -6.2759, 106.9204 -6.09, 106.6896 -6.09, 106.6896 -6.2759))"
    # poly = "POLYGON((106.8156 -6.1495,106.8285 -6.1495,106.8285 -6.1413,106.8156 -6.1413,106.8156 -6.1495))"
    # poly = "POLYGON((-44.1434 -20.1344,-44.1125 -20.1344,-44.1125 -20.1128,-44.1434 -20.1128,-44.1434 -20.1344))"
    # poly = "POLYGON((106.5233 -6.2917,106.9387 -6.2917,106.9387 -6.0364,106.5233 -6.0364,106.5233 -6.2917))"
    # poly = "POLYGON((106.5224 -6.0993,106.5479 -6.3363,106.9566 -6.2263,106.8374 -5.6928,106.4968 -5.7521,106.5224 -6.0993))"
    poly = "POLYGON((106.7384 -6.247,106.8686 -6.247,106.8686 -6.2147,106.7384 -6.2147,106.7384 -6.247))"
    Subset = create_subset(Goldstein_phasefiltering, poly)


    print('Export to Snaphu')





    # Subset = Goldstein_phasefiltering
    HashMap = jpy.get_type('java.util.HashMap')
    parameters = HashMap()
    parameters.put("targetFolder", '/mnt/d/PROJECTS/grace/SAR/output/snaphu')
    result_SNE=GPF.createProduct("SnaphuExport", parameters, Subset)

    ProductIO.writeProduct(result_SNE, '/mnt/d/PROJECTS/grace/SAR/output/snaphu/', "Snaphu")

    print('Snaphu unwrapping')
    unwrap_snaphu('/mnt/d/PROJECTS/grace/SAR/output/snaphu')

    print('Import unwrapped hdr to SNAP')
    importedProduct = import_snaphu(Subset,  '/mnt/d/PROJECTS/grace/SAR/output/snaphu/')
    print('successfully imported')
    #
    #
    # # print('create even smaller subset of importdProduct')
    # # poly = "POLYGON((-44.1202760265804 -20.122412144896483, -44.1227375652734 -20.118146220374225, -44.12117821949503 -20.116219314519526," \
    # #        " -44.117224164128444 -20.12200003208363, -44.117224164128444 -20.12200003208363, -44.1202760265804 -20.122412144896483))"
    # Subset2 = create_subset(importedProduct, poly)
    #
    print('Calculate displacement from phase')
    displacementProduct = PhaseToDisplacement(importedProduct)
    print('success')


    print('Merge to add coherence back into displacementProduct')
    mergedProduct = merge(importedProduct, displacementProduct)

    print('Perform terrain correction')
    terrainCorrectedProduct = terrain_correction(mergedProduct)

    print('Perform band maths to mask displacements with coherence less than a set threshold')

    maskedDisplacementProduct = bandMathsProduct(terrainCorrectedProduct)

    print('second merge to put coherence with displacement')
    mergedProduct2 = merge(maskedDisplacementProduct, terrainCorrectedProduct)
    write(mergedProduct2, fileOut)
    write_netcdf(mergedProduct2, fileOut)

    print('dispose of products to prevent memory leakage')
    product_1.dispose()
    product_2.dispose()
    product_TOPSAR_1.dispose()
    product_TOPSAR_2.dispose()
    product_orbitFile_1.dispose()
    product_orbitFile_2.dispose()
    backGeocoding.dispose()
    interferogram_formation.dispose()
    TOPSAR_deburst.dispose()
    TOPO_phase_removal.dispose()
    MultiLook.dispose()
    Goldstein_phasefiltering.dispose()
    Subset.dispose()
    importedProduct.dispose()
    # Subset2.dispose()
    displacementProduct.dispose()
    mergedProduct.dispose()
    maskedDisplacementProduct.dispose()
    mergedProduct2.dispose()

    print('Delete snaphu output')
    shutil.rmtree(snaphuDir)

path2project = os.path.abspath(os.path.join(os.path.dirname(__file__)))

path2input = os.path.join(path2project,'input')
infile_list = os.listdir(path2input)
infile_list = [f for f in infile_list if f.endswith('.zip')]

"""iterate through input files in pairs of two in order to create a time series"""
for master, slave in zip(infile_list, infile_list[1::]):
    print('master, slave: ', master, slave)

    fn1 = os.path.join(path2input, master)
    fn2 = os.path.join(path2input, slave)
    date_start = master.split('_')[6]
    date_end = slave.split('_')[6]

    outputPath = os.path.join(path2project, 'output')
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    snaphuDir = os.path.join(outputPath, 'snaphu')
    fileOut = os.path.join(outputPath, 'Masked_Displacement_%s_%s' % (date_start, date_end))

    insar_pipeline(fn1, fn2)

    gc.collect()



### USEFUL LINKS
"""SAR data (fn1 and fn2) were downloaded from https://search.asf.alaska.edu/#/
    options used on VERTEX site: File Types: SLC Beam Modes: IW Polarizations: VV+VH Flight Dir: Ascending Dataset: SA"""
"""https://forum.step.esa.int/t/slower-snappy-processing/6354/5"""
"""https://senbox.atlassian.net/wiki/spaces/SNAP/pages/19300362/How+to+use+the+SNAP+API+from+Python"""
"""https://gist.github.com/braunfuss/41caab61817fbae71a25bba82a02a8c0"""
"""https://forum.step.esa.int/t/snappy-sarsim-terrain-correction-runtimeerror-java-lang-nullpointerexception/8804"""
"""http://step.esa.int/docs/tutorials/S1TBX%20Stripmap%20Interferometry%20with%20ERS%20Tutorial.pdf"""
"""https://forum.step.esa.int/t/call-productset-reader-and-create-stack-in-snap/4290/3"""
"""!! Had to copy the SNAPPY module to py36 environment on Ubuntu otherwise IO does not function correctly"""