import webbrowser
import ee
import matplotlib.pyplot as plt
from skimage.io import imread
import os

ee.Initialize()
image = ee.Image('srtm90_v4')
print(image.getInfo())


# Access a specific image
image = ee.Image('LANDSAT/LC08/C01/T1_TOA/LC08_044034_20140318'); #Landsat 8 image, with Top of Atmosphere processing, on 2014/03/18

# Access a collection
collection = 'LANDSAT/LC08/C01/T1_TOA' #Landsat 7 raw images collection


area_reading = list([(13.6, 50.96), (13.9, 50.96), (13.9, 51.12), (13.6, 51.12), (13.6, 50.96)])
area_reading = ee.Geometry.Polygon(area_reading)
time_range_reading = ['2014-07-28', '2014-08-05']

collection_reading = ('LANDSAT/LC08/C01/T1')
print(type(area_reading))

def obtain_image_landsat_composite(collection, time_range, area):
    """ Selection of Landsat cloud-free composites in the Earth Engine library
    See also: https://developers.google.com/earth-engine/landsat

    Parameters:
        collection (): name of the collection
        time_range (['YYYY-MT-DY','YYYY-MT-DY']): must be inside the available data
        area (ee.geometry.Geometry): area of interest

    Returns:
        image_composite (ee.image.Image)
     """
    collection = ee.ImageCollection(collection)

    ## Filter by time range and location
    collection_time = collection.filterDate(time_range[0], time_range[1])
    image_area = collection_time.filterBounds(area)
    image_composite = ee.Algorithms.Landsat.simpleComposite(image_area, 75, 3)
    return image_composite

def obtain_image_median(collection, time_range, area):
    """ Selection of median from a collection of images in the Earth Engine library
    See also: https://developers.google.com/earth-engine/reducers_image_collection

    Parameters:
        collection (): name of the collection
        time_range (['YYYY-MT-DY','YYYY-MT-DY']): must be inside the available data
        area (ee.geometry.Geometry): area of interest

    Returns:
        image_median (ee.image.Image)
     """
    collection = ee.ImageCollection(collection)

    ## Filter by time range and location
    collection_time = collection.filterDate(time_range[0], time_range[1])
    image_area = collection_time.filterBounds(area)
    image_median = image_area.median()
    return image_median

def obtain_image_sentinel(collection, time_range, area):
    """ Selection of median, cloud-free image from a collection of images in the Sentinel 2 dataset
    See also: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2

    Parameters:
        collection (): name of the collection
        time_range (['YYYY-MT-DY','YYYY-MT-DY']): must be inside the available data
        area (ee.geometry.Geometry): area of interest

    Returns:
        sentinel_median (ee.image.Image)
     """
#First, method to remove cloud from the image
    def maskclouds(image):
        band_qa = image.select('QA60')
        cloud_mask = ee.Number(2).pow(10).int()
        cirrus_mask = ee.Number(2).pow(11).int()
        mask = band_qa.bitwiseAnd(cloud_mask).eq(0) and(
            band_qa.bitwiseAnd(cirrus_mask).eq(0))
        return image.updateMask(mask).divide(10000)

    sentinel_filtered = (ee.ImageCollection(collection).
                         filterBounds(area).
                         filterDate(time_range[0], time_range[1]).
                         filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).
                         map(maskclouds))

    sentinel_median = sentinel_filtered.median()
    return sentinel_median

composite_reading = obtain_image_landsat_composite(collection_reading, time_range_reading, area_reading)


print(composite_reading.select(['B4','B3','B2']).getInfo())


def get_region(geom):
    """Get the region of a given geometry, needed for exporting tasks.

    Parameters:
        geom (ee.Geometry, ee.Feature, ee.Image): region of interest

    Returns:
        region (list)
    """
    if isinstance(geom, ee.Geometry):
        region = geom.getInfo()["coordinates"]
    elif isinstance(geom, ee.Feature, ee.Image):
        region = geom.geometry().getInfo()["coordinates"]
    elif isinstance(geom, list):
        condition = all([isinstance(item) == list for item in geom])
        if condition:
            region = geom
    return region


region_reading = get_region(area_reading)

def get_url(name, image, scale, region):
    """It will open and download automatically a zip folder containing Geotiff data of 'image'.
    If additional parameters are needed, see also:
    https://github.com/google/earthengine-api/blob/master/python/ee/image.py

    Parameters:
        name (str): name of the created folder
        image (ee.image.Image): image to export
        scale (int): resolution of export in meters (e.g: 30 for Landsat)
        region (list): region of interest

    Returns:
        path (str)
     """
    path = image.getDownloadURL({
        'name':(name),
        'scale': scale,
        'region':(region)
        })

    webbrowser.open_new_tab(path)
    return path

url_reading = get_url('reading', composite_reading, 30, region_reading)

print(url_reading)

DATA_DIR = "C:\\Users\\carlhaines\\Downloads"


reading = os.path.join(DATA_DIR, 'reading', 'reading.B1.tif') #B4 of Dresden example

print(reading)
# TODO find way to unzip download file or keep image within python
# Following should work for unzipped folder
image_reading = imread(reading)
plt.figure(figsize=(10, 10))
plt.imshow(image_reading, cmap='gray', interpolation='nearest')
plt.axis()
plt.show()

#Crop the image
image_reading_crop= image_reading[300:700, 600:1400]
plt.figure(figsize=(10, 10))
plt.imshow(image_reading_crop, cmap='gray', interpolation='nearest')
plt.axis()
plt.show()

# TODO Debug following code to combine RGB bands
"""
from IPython.display import Image
image = composite_reading.reduce('median')
PERCENTILE_SCALE = 30  # Resolution in meters to compute the percentile at
percentiles = image.reduceRegion(ee.Reducer.percentile([0, 100], ['min', 'max']), region_reading, PERCENTILE_SCALE).getInfo()
# Extracting the results is annoying because EE prepends the channel name
minVal = [val for key, val in percentiles.items() if 'min' in key]
# splitVal = next(val for key, val in percentiles.items() if 'split' in key)
maxVal = [val for key, val in percentiles.items() if 'max' in key]
print(minVal)
print(maxVal)
reduction = image.visualize(bands= ['B4', 'B3', 'B2'],
                            min=list(reversed(minVal)), # reverse since bands are given in the other way (b2,b3,4b)
                            max=list(reversed(maxVal)),
                            gamma=1)
                            
"""