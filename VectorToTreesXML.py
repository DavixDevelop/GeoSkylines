from qgis.core import *
from random import shuffle
from pathlib import Path
import xml.etree.cElementTree as ET
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor
import math
import random
from datetime import datetime
import traceback

CATEGORY = 'VectorToTreesXML'

#Name of the layer that contains the composition of the forest
polygon_layer_name = "ForestLayerName"

#How many trees you wish to place on the map
total_trees_count = 1800000

#Name of attributes that determine the composition of the forest in percentages (all together add up to 100%)
attributes = [ "oak1", "spruce2"]
#ID's of above attributes that will be written to the xml file instead of the full attribute name
#These ID's are then used in import_export.txt to configure what tree assets to place
attributes_ids = [1, 2]
#Colors of above attributes used in the points layer, to visualize the placement of trees on the map 
attributes_colors = ["#f82bde", "#20a8a2"]

#Extent of your IRL map. Must be in meters with a size of 17280x17280 meters
#Make sure your polygon layer lies within this extent and It's coordinate reference system uses meters as unit as well
#Left, Right, Top, Bottom 
extent = [ 512005, 529285, 130897, 113617]

#Path to the output xml file
treesXML_path = "C:/Program Files (x86)/Steam/steamapps/common/Cities_Skylines/Files/trees.xml"

#Change this to True if you wish to only preview how the trees will be placed in single feature/polygon (the first feature in the layer)
#Changing this to True will also not generate the treesXML file
preview_mode = False

#How many trees you wish to place outside the play area
#In turn, total_trees_count get subtracted from this
non_play_area_tree_count = 550000

#Play Area Extent = Extent - Play Area Offset
#Determines where to distribute the non_play_area_tree_count of trees
#The trees in the non play area get distributed based on the distance from the play area, meaning
#the further feature/polygon is from the play area, the less dense it is
#This is done so that there are as much trees as possible in the play area, to make the forests more denser
#The offset should 3840 ((17280 / 9) * 2), but a lower value of 3640 creates a less hard edge
play_area_offset = 3640

class TreesXML:
    def __init__(self, listID):
        self.Width = 17280
        self.Height = 17280
        self.TreeCount = 0
        self.Mode = 'vector'
        self.ListID = listID
        self.Buffers = []

class BufferedTreesCollection:
    def __init__(self):
        self.BufferedTrees = []

class BufferedTrees:
    def __init__(self, id, positions):
        self.ID = id
        self.Positions = positions

class Position:
    def __init__(self, x, y):
        self.X = x
        self.Y = y

class TaskData:
    def __init__(self, layerName, playAreaTreesCount, nonPlayAreaTreesCount, fields, fieldIDS, fieldColors, playAreaExtent, mapAreaExtent, outputPath, treeXmlLayerName, treeXmlPointsLayerName, previewMode):
        self.layerName = layerName
        self.playAreaTreesCount = playAreaTreesCount
        self.nonPlayAreaTreesCount = nonPlayAreaTreesCount
        self.fields = fields
        self.fieldIDS = fieldIDS
        self.fieldColors = fieldColors
        self.playAreaExtent = playAreaExtent
        self.mapAreaExtent = mapAreaExtent
        self.outputPath = outputPath
        self.treeXmlLayerName = treeXmlLayerName
        self.treeXmlPointsLayerName = treeXmlPointsLayerName
        self.previewMode = previewMode
        self.timeStart = datetime.now()
        self.generatedCount = 0

    def setPointsLayer(self, pointsLayer, renderer):
        self.pointsLayer = pointsLayer
        self.renderer = renderer

    def setGeneratedCount(self, generatedCount):
        self.generatedCount = generatedCount
        

def serializeTreeXML(treeXML):
    namespace = {
        'xmlns:xsi':'http://www.w3.org/2001/XMLSchema-instance',
        'xmlns:xsd':'http://www.w3.org/2001/XMLSchema'
    }

    root = ET.Element("TreesXML", namespace)
    width = ET.SubElement(root, "Width")
    width.text = str(treeXML.Width)
    height = ET.SubElement(root, "Height")
    height.text = str(treeXML.Height)
    treeCount = ET.SubElement(root, "TreeCount")
    treeCount.text = str(treeXML.TreeCount)
    mode = ET.SubElement(root, "Mode")
    mode.text = treeXML.Mode

    listID = ET.SubElement(root, "ListID")
    for i in treeXML.ListID:
        num = ET.SubElement(listID, "int")
        num.text = str(i)
    
    buffers = ET.SubElement(root, "Buffers")
    for _col in treeXML.Buffers:
        col = ET.SubElement(buffers, "BufferedTreesCollection")
        bufferedTrees = ET.SubElement(col, "BufferedTrees")
        for _buff in _col.BufferedTrees:
            buff = ET.SubElement(bufferedTrees, "BufferedTrees")
            id = ET.SubElement(buff, "ID")
            id.text = str(_buff.ID)
            positions = ET.SubElement(buff, "Positions")
            for _position in _buff.Positions:
                position = ET.SubElement(positions, "Position")
                x = ET.SubElement(position, "X")
                x.text = str(_position.X)
                y = ET.SubElement(position, "Y")
                y.text = str(_position.Y)
    
    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)

    return tree

# Get the intersecting point if the point lies on the line
def getIntersection(k, n, x1, y1, x2, y2, i):
    if x1 == x2:
        i[0] = x1
        i[1] = k * i[0] + n
        if i[1] >= y1 and i[1] <= y2:
            return True
    
    if y1 == y2:
        i[1] = y1
        i[0] = (n - i[1]) / -k
        if i[0] >= x1 and i[0] <= x2:
            return True

    return False

#Get the normalized distance (0-1) of the point between the play area and map area extent 
def getNormalizedDistance(point, map_center, play_area_extent, map_area_extent):
    #Calculate closest point of the point to the edge of the play area and map area
    pi = [0,0]
    mi = [0,0]

    if(point.x() == map_center.x()):
        #Point is vertical perpendicular to map center 
        pi[0] = point.x()
        mi[0] = point.x()

        #Check if point lies above play area
        if point.y() >= play_area_extent.yMaximum():
            pi[1] = play_area_extent.yMaximum()
            mi[1] = map_area_extent.yMaximum()
        #Else it lies underneath play area
        else:
            pi[1] = play_area_extent.yMinimum()
            mi[1] = map_area_extent.yMinimum()

    elif(point.y() == map_center.y()):
        #Point is horizontal perpendicular to map center
        pi[1] = point.y()
        mi[1] = point.y()
        #Check if point lies to the left of the play area
        if point.x() <= play_area_extent.xMinimum():
            pi[0] = play_area_extent.xMinimum()
            mi[0] = map_area_extent.xMinimum()
        #Else it lies to the right side of the play area
        else:
            pi[0] = play_area_extent.xMaximum()
            mi[0] = map_area_extent.xMaximum()

    else:
        k = (point.y() - map_center.y()) / (point.x() - map_center.x())
        n = point.y() - k * point.x()

        #Calculate intersection point with left side of play area
        if point.x() <= play_area_extent.xMinimum() and getIntersection(k, n, play_area_extent.xMinimum(), play_area_extent.yMinimum(), play_area_extent.xMinimum(), play_area_extent.yMaximum(), pi):
            getIntersection(k, n, map_area_extent.xMinimum(), map_area_extent.yMinimum(), map_area_extent.xMinimum(), map_area_extent.yMaximum(), mi)
        #Calculate intersection point with right side of play area
        elif point.x() >= play_area_extent.xMaximum() and getIntersection(k, n, play_area_extent.xMaximum(), play_area_extent.yMinimum(), play_area_extent.xMaximum(), play_area_extent.yMaximum(), pi):
            getIntersection(k, n, map_area_extent.xMaximum(), map_area_extent.yMinimum(), map_area_extent.xMaximum(), map_area_extent.yMaximum(), mi)
        #Calculate intersection point with top side of play area
        elif point.y() >= play_area_extent.yMaximum() and getIntersection(k, n, play_area_extent.xMinimum(), play_area_extent.yMaximum(), play_area_extent.xMaximum(), play_area_extent.yMaximum(), pi):
            getIntersection(k, n, map_area_extent.xMinimum(), map_area_extent.yMaximum(), map_area_extent.xMaximum(), map_area_extent.yMaximum(), mi)
        #Calculate intersection point with bottom side of play area
        elif point.y() <= play_area_extent.yMinimum() and getIntersection(k, n, play_area_extent.xMinimum(), play_area_extent.yMinimum(), play_area_extent.xMaximum(), play_area_extent.yMinimum(), pi):
            getIntersection(k, n, map_area_extent.xMinimum(), map_area_extent.yMinimum(), map_area_extent.xMaximum(), map_area_extent.yMinimum(), mi)

    distance_to_map_area = abs(math.sqrt(math.pow(mi[0] - point.x(), 2) + math.pow(mi[1] - point.y(), 2)))
    distance_to_play_area= abs(math.sqrt(math.pow(point.x() - pi[0], 2) + math.pow(point.y() - pi[1], 2)))

    return distance_to_play_area / (distance_to_map_area + distance_to_play_area) 

#Create a equal grid points with a jitter on top of the polygon
def genJitterGrid(polygon, map_area_extent, total_points, jitter):
    points = []

    bbo = polygon.boundingBox()

    #Determine the min distances
    nx = (bbo.width() / bbo.height() * total_points) ** 0.5
    ny = total_points / nx

    min_distance_x = bbo.width() / nx
    min_distance_y = bbo.height() / ny
    
    #print('min_dx: {} | min_dy: {} | po: {}, | wid: {} | hei: {}'.format(min_distance_x, min_distance_y, total_points, bbo.width(), bbo.height()))
    
    rx = 0
    ry = 0

    x = bbo.xMinimum()
    while x < bbo.xMaximum():
        y = bbo.yMinimum()
        while y < bbo.yMaximum():
            rx = x + random.uniform(-jitter, jitter)
            ry = y + random.uniform(-jitter, jitter)

            if polygon.contains(rx, ry) and (rx > map_area_extent.xMinimum() and rx < map_area_extent.xMaximum() and ry < map_area_extent.yMaximum() and ry > map_area_extent.yMinimum()):
                points.append(QgsPointXY(rx, ry))
            
            y += min_distance_y
        x += min_distance_x

    return points



def genTreeXML(task, taskData):
    try:
        #Center point of map area
        map_center = taskData.mapAreaExtent .center()

        layer = QgsProject.instance().mapLayersByName(taskData.layerName)[0]

        #Sum the area field of all features inside the play area, and outside
        sum_of_all_play_area = 0
        sum_of_all_non_play_area = 0
        for feature in layer.getFeatures():
            feature_area = feature.geometry().area()
            if feature.geometry().boundingBox().intersects(taskData.playAreaExtent):
                sum_of_all_play_area += feature_area
            else:
                sum_of_all_non_play_area += feature_area

        treeXML = TreesXML(taskData.fieldIDS)

        #Create new vector point layer
        layer_crs = layer.crs().authid()
        points_layer = QgsVectorLayer('Point?crs={epsg}'.format(epsg=layer_crs), taskData.treeXmlPointsLayerName, 'memory')
        data_provider = points_layer.dataProvider()

        #Enter edit mode
        points_layer.startEditing()

        #Add fields
        data_provider.addAttributes([
            QgsField('fieldType', QVariant.String)
        ])

        points_layer.updateFields()

        task.setProgress(0)
        
        feature_id = 0

        for feature in layer.getFeatures():
            feature_id += 1
            task.setProgress((feature_id * 100) / layer.featureCount())

            geom = feature.geometry()
            center_point = geom.centroid().asPoint()

            points_per_feature = 0

            #Check if feature lies withing play area
            if feature.geometry().boundingBox().intersects(taskData.playAreaExtent):
                points_per_feature = int(taskData.playAreaTreesCount * (geom.area() / sum_of_all_play_area))
            else:
                #Calculate the area weight
                area_weight = geom.area() / sum_of_all_non_play_area
            
                #Calculate the normalized distance (0-1) to the closeness of the play area
                normalized_distance = getNormalizedDistance(center_point, map_center, taskData.playAreaExtent, taskData.mapAreaExtent)

                #Closer features get higher weight
                distance_weight = 1 - normalized_distance

                points_per_feature = int(taskData.nonPlayAreaTreesCount * area_weight * distance_weight)

            #Get the attribute percentages
            percentages = [feature[field] for field in taskData.fields]
            counts = [round(points_per_feature * (p / 100)) for p in percentages]

            #Generate a list of id labels based on counts
            id_labels = []
            for i, count in enumerate(counts):
                id_labels.extend([task_data.fieldIDS[i]] * count)

            points_per_feature = len(id_labels)

            if points_per_feature > 0:

                #Shuffle the id labels randomly
                shuffle(id_labels)

                points = []

                if points_per_feature > 8:
                    #Generate grid with a jitter inside the polygon
                    points.extend(genJitterGrid(geom, taskData.mapAreaExtent, points_per_feature, 2))
                
                #Calculate the random number of points from the leftover
                random_points_per_feature = points_per_feature - len(points)

                if random_points_per_feature > 0:
                    #Generate random points inside the polygon
                    points.extend(geom.randomPointsInPolygon(random_points_per_feature, 23))

                col = BufferedTreesCollection()

                treesPerID = {}

                for i in range(len(points)):
                    id = id_labels[i]
                    point = points[i]

                    _pos = []
                    if id in treesPerID: 
                        _pos = treesPerID[id]
                    
                    _pos.append(Position(point.x() - taskData.mapAreaExtent.xMinimum() - 8640.0, point.y() - taskData.mapAreaExtent.yMinimum() - 8640.0))
                    treesPerID[id] = _pos

                    point_feature = QgsFeature()
                    point_feature.setGeometry(QgsGeometry.fromPointXY(point))
                    point_feature.setAttributes([str(id)])
                    data_provider.addFeature(point_feature)

                
                for _id, _positions in treesPerID.items():
                    col.BufferedTrees.append(BufferedTrees(_id, _positions))

                treeXML.TreeCount += points_per_feature
                treeXML.Buffers.append(col)

                points_layer.commitChanges()

                if taskData.previewMode:
                    break

        taskData.setGeneratedCount(treeXML.TreeCount)

        if not taskData.previewMode:
            xmlTree = serializeTreeXML(treeXML)
            xmlTree.write(taskData.outputPath, encoding='utf-8', xml_declaration=True)

        #Create categorized symbology
        fieldCategories = []

        for index in range(len(taskData.fields)):
            #Define the style for the category
            layer_style = {}
            layer_style['color'] = taskData.fieldColors[index]
            layer_style['outline'] = "#000000"
            layer_style['size'] = "8.0"
            layer_style['size_unit'] = "MapUnit"
            layer_style['size_map_unit_scale'] = "0,1,0,0,0,0"
            point_symbol = QgsMarkerSymbol.createSimple(layer_style)

            #Create renderer category
            category = QgsRendererCategory(str(taskData.fieldIDS[index]), point_symbol.clone(), str(taskData.fields[index]))
            fieldCategories.append(category)

        renderer = QgsCategorizedSymbolRenderer('fieldType', fieldCategories)

        if points_layer is not None:
            taskData.setPointsLayer(points_layer, renderer)
        
    except Exception as e:
        print('{}: Error: {}'.format(CATEGORY, str(e)))
        traceback.print_exc()
        return None

    return taskData


def genComplete(task, taskData=None):
    if taskData is not None:
        time_end = datetime.now()
        eclipsed = (time_end - taskData.timeStart).total_seconds() / 60.0
        minutes = math.floor(eclipsed)
        seconds = math.floor((eclipsed - minutes) * 60)
        print('{}: Done generating {} trees for treesXML file in {} minutes, {} seconds'.format(CATEGORY, taskData.generatedCount, minutes, seconds))

        if taskData.pointsLayer is not None:
            points_layer = taskData.pointsLayer
            QgsProject.instance().addMapLayer(points_layer)

            if taskData.renderer is not None:
                points_layer.setRenderer(taskData.renderer)
            points_layer.triggerRepaint()


if extent[1] - extent[0] == 17280 and extent[2] - extent[3] == 17280:
    play_area_tree_count = total_trees_count - non_play_area_tree_count

    #Calculate play area extent [Left, Bottom, Right, Top]
    play_area_extent = QgsRectangle(extent[0] + play_area_offset, extent[3] + play_area_offset, extent[1] - play_area_offset, extent[2] - play_area_offset)
    map_area_extent = QgsRectangle(extent[0], extent[3], extent[1], extent[2])

    #Determine filename of the tree XML file
    treeXML_layer_name = Path(treesXML_path).stem

    #Check if vector point layer already exists
    points_layers_name = '{ln}_points'.format(ln=treeXML_layer_name)
    for l in QgsProject.instance().mapLayers():
        if l.startswith(points_layers_name):
            QgsProject.instance().removeMapLayer(l)

    task_data = TaskData(polygon_layer_name, play_area_tree_count, non_play_area_tree_count, attributes, attributes_ids, attributes_colors, play_area_extent, map_area_extent, treesXML_path, treeXML_layer_name, points_layers_name, preview_mode)

    globals()['treesTask'] = QgsTask.fromFunction('Generate treeXML file', genTreeXML, on_finished=genComplete, taskData=task_data)
    QgsApplication.taskManager().addTask(globals()['treesTask'])
else:
    print('{}: Extent is not 17280x17280 meters'.format(CATEGORY))
