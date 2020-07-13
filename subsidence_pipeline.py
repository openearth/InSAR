import os
from snappy import GPF
from snappy import ProductIO
from snappy import HashMap
from snappy import jpy
from snappy import WKTReader
import subprocess
import glob

# Hashmap is used to provide access to all JAVA operators
HashMap = jpy.get_type('java.util.HashMap')
parameters = HashMap()

def read(filename):
    return ProductIO.readProduct(filename)

def write(product, filename):
    ProductIO.writeProduct(product, filename, "BEAM-DIMAP")

def write_netcdf(product, filename):
    ProductIO.writeProduct(product, filename, 'NetCDF4-CF')

def topsar_split(product):
    parameters.put('subswath', 'IW2')
    parameters.put('selectedPolarisations', 'VV')
    return GPF.createProduct("TOPSAR-Split", parameters, product)

def apply_orbit_file(product):
    parameters.put("Orbit State Vectors", "Sentinel Precise (Auto Download)")
    parameters.put("Polynomial Degree", 3)
    return GPF.createProduct("Apply-Orbit-File", parameters, product)


def back_geocoding(product):
    parameters.put("Digital Elevation Model", "SRTM 1Sec HGT (Auto Download)")
    parameters.put("DEM Resampling Method", "BICUBIC_INTERPOLATION")
    parameters.put("Resampling Type", "BISINC_5_POINT_INTERPOLATION")
    parameters.put("Mask out areas with no elevation", True)
    parameters.put("Output Deramp and Demod Phase", False)
    return GPF.createProduct("Back-Geocoding", parameters, product)


def interferogram(product):
    parameters.put("Subtract flat-earth phase", True)
    parameters.put("Degree of \"Flat Earth\" polynomial", 5)
    parameters.put("Number of \"Flat Earth\" estimation points", 501)
    parameters.put("Orbit interpolation degree", 3)
    parameters.put("Include coherence estimation", True)
    parameters.put("Square Pixel", False)
    parameters.put("Independent Window Sizes", False)
    parameters.put("Coherence Azimuth Window Size", 10)
    parameters.put("Coherence Range Window Size", 10)
    return GPF.createProduct("Interferogram", parameters, product)

def topsar_deburst(product):
    parameters.put("Polarisations", "VV")
    return GPF.createProduct("TOPSAR-Deburst", parameters, product)

def topophase_removal(product):
    parameters.put("Orbit Interpolation Degree", 3)
    parameters.put("Digital Elevation Model", "SRTM 1Sec HGT (Auto Download)")
    parameters.put("Tile Extension[%]", 100)
    parameters.put("Output topographic phase band", True)
    parameters.put("Output elevation band", False)
    return GPF.createProduct("TopoPhaseRemoval", parameters, product)


def goldstein_phasefiltering(product):
    parameters.put("Adaptive Filter Exponent in(0,1]:", 1.0)
    parameters.put("FFT Size", 64)
    parameters.put("Window Size", 3)
    parameters.put("Use coherence mask", False)
    parameters.put("Coherence Threshold in[0,1]:", 0.4)
    return GPF.createProduct("GoldsteinPhaseFiltering", parameters, product)

def create_subset(product):
    """obtain polygon with VERTEX"""
    wkt = "POLYGON((4.3108 51.8655,4.416 51.8655,4.416 51.9163,4.3108 51.9163,4.3108 51.8655))"
    geom = WKTReader().read(wkt)
    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geom)
    return GPF.createProduct('Subset', parameters, product)

def unwrap_snaphu_Displacement(product, temp_path):
    parameters = HashMap()
    parameters_snaphu = HashMap()
    parameters_snaphu.put("targetFolder", str(temp_path))
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
    result_PD = GPF.createProduct("PhaseToDisplacement", parameters, result_SI)
    return result_PD

### TERRAIN CORRECTION
def terrain_correction(product):
    parameters.put('demResamplingMethod', 'BILINEAR_INTERPOLATION') #alternatively use 'NEAREST_NEIGHBOUR'
    parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('demName', 'SRTM 3Sec')
    parameters.put('pixelSpacingInMeter', 15.0)
    parameters.put('sourceBands', 'displacement')
    parameters.put('saveLocalIncidenceAngle', True)
    parameters.put('saveLatLon', True)
    # parameters.put('incidenceAngle', 'Use local incidence angle from Ellipsoid')
    return GPF.createProduct("Terrain-Correction", parameters, product)

def bandMathsProduct(product):
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
    product_TOPSAR_1 = topsar_split(product_1)
    product_TOPSAR_2 = topsar_split(product_2)

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

    print('Goldstein filtering')
    Goldstein_phasefiltering = goldstein_phasefiltering(TOPO_phase_removal)

    print('Create subset')
    Subset = create_subset(Goldstein_phasefiltering)

    print('Snaphu unwrapping and displacement calculation')
    outputPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    snaphuPath = os.path.join(outputPath, 'snaphu')

    Displacement = unwrap_snaphu_Displacement(Subset, snaphuPath)

    print('Perform terrain correction')
    terrainCorrected = terrain_correction(Displacement)

    print('Calculate vertical displacement')
    verticalDisplacement = bandMathsProduct(terrainCorrected)

    print('Write result to NetCDF4-CF file')
    write_netcdf(verticalDisplacement, os.path.join(outputPath,'Vertical_Displacement'))
    print('Write result to BEAM-DIMAP')
    write(verticalDisplacement, os.path.join(outputPath,'Vertical_Displacement'))


path2input = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'input'))
fn1 = os.path.join(path2input, 'S1A_IW_SLC__1SDV_20150402T173247_20150402T173314_005308_006B81_76C8.zip')
fn2 = os.path.join(path2input, 'S1A_IW_SLC__1SDV_20150601T173250_20150601T173317_006183_0080D8_1DFD.zip')
insar_pipeline(fn1, fn2)

### USEFUL LINKS
"""SAR data (fn1 and fn2) were downloaded from https://search.asf.alaska.edu/#/
    options used on VERTEX site: File Types: SLC Beam Modes: IW Polarizations: VV+VH Flight Dir: Ascending Dataset: SA"""
"""https://forum.step.esa.int/t/slower-snappy-processing/6354/5"""
"""https://senbox.atlassian.net/wiki/spaces/SNAP/pages/19300362/How+to+use+the+SNAP+API+from+Python"""
"""https://gist.github.com/braunfuss/41caab61817fbae71a25bba82a02a8c0"""
"""https://forum.step.esa.int/t/snappy-sarsim-terrain-correction-runtimeerror-java-lang-nullpointerexception/8804"""
