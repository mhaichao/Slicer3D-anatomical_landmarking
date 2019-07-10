# TU Wien, MedUni Wien
# Haichao Miao
# miao@cg.tuwien.ac.at

from __main__ import vtk, qt, ctk, slicer
from Landmark import Landmark
from Spline import Spline
from xml.dom import minidom
#import string
import numpy

#
# JawLandmarking
#

class JawLandmarking:
    def __init__(self, parent):
        parent.title = "Jaw Landmarking"
        parent.categories = ["Landmarking"]
        parent.dependencies = []
        parent.contributors = ["Haichao Miao"]
        parent.helpText = """
    """
        parent.acknowledgementText = """
    """  # replace with organization, grant and thanks.
        self.parent = parent


#
# qJawLandmarkingWidget
#

class JawLandmarkingWidget:
    def __init__(self, parent=None):
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()
        if not parent:
            self.setup()
            self.parent.show()

        self.createContent()

    ### Setup ###

    def createContent(self):
        self.fidObserve = None
        self.landmarks = []
        self.splines = []
        self.placingStarted = False
        self.selectedTableRow = 0
        self.curNumberOfFids = 0
        self.landmarkNamesInTable = []
        self.exportFile = 'C:/Development/morphometry/export.csv'

        self.parseLandmarksAndSplines()

    def setup(self):

        print ("setup")
        # Collapsible button
        self.sampleCollapsibleButton = ctk.ctkCollapsibleButton()
        self.sampleCollapsibleButton.text = "A collapsible button"
        self.layout.addWidget(self.sampleCollapsibleButton)

        self.sampleFormLayout = qt.QFormLayout(self.sampleCollapsibleButton)

        self.btnBeginPlacingLandmarks = qt.QPushButton("Begin Placing")
        self.btnBeginPlacingLandmarks.toolTip = "Placing Anatomical Landmarks"
        self.sampleFormLayout.addWidget(self.btnBeginPlacingLandmarks)
        self.btnBeginPlacingLandmarks.connect('clicked(bool)', self.beginPlacing)

        self.layout.addStretch(1)

        markup = slicer.modules.markups.logic()
        markup.AddNewFiducialNode()

        self.table = qt.QTableWidget()
        self.table.setRowCount(1)
        self.table.setColumnCount(5)
        self.table.horizontalHeader().setResizeMode(qt.QHeaderView.Stretch)
        self.table.setSizePolicy (qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Preferred)
        self.table.setMinimumWidth(400)
        self.table.setMinimumHeight(215)
        self.table.setMaximumHeight(215)
        horizontalHeaders = ["Landmark", "Fiducial ID", "x", "y", "z"]
        self.table.setHorizontalHeaderLabels(horizontalHeaders)
        self.table.itemSelectionChanged.connect(self.onTableCellClicked)
        self.sampleFormLayout.addWidget(self.table)

        self.deleteFid = qt.QPushButton("Delete Selected Fiducial")
        self.deleteFid.connect('clicked(bool)', self.deleteFiducial)
        #self.sampleFormLayout.addWidget(self.deleteFid)

        fiducialNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
        self.fidObserve = fiducialNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.placeFiducialAsLandmark)

        self.btnComputeSplines = qt.QPushButton("Compute Splines")
        self.btnComputeSplines.toolTip = ""
        self.sampleFormLayout.addWidget(self.btnComputeSplines)
        self.btnComputeSplines.connect('clicked(bool)', self.computeSplines)

        self.btnExportSplines = qt.QPushButton("Export Splines")
        self.btnExportSplines.toolTip = ""
        self.sampleFormLayout.addWidget(self.btnExportSplines)
        self.btnExportSplines.connect('clicked(bool)', self.exportSplines)

        self.initializeTable()

    def initializeTable(self):
        print("initialize table")

        self.table.setRowCount(len(self.landmarks))

        i = 0
        for landmark in self.landmarks:
            landmarkName = qt.QTableWidgetItem(landmark.name)
            landmarkPlaced = qt.QTableWidgetItem(str(landmark.placed))
            self.landmarkNamesInTable.append(landmark.name)

            self.table.setItem(i, 0, landmarkName)
            self.table.setItem(i, 2, 0)
            self.table.setItem(i, 3, 0)
            self.table.setItem(i, 4, 0)
            i += 1
        self.table.selectRow(self.selectedTableRow)

    def parseLandmarksAndSplines(self):
        print("parse landmarks from xml")
        doc = minidom.parse('C:/Development/morphometry/Landmarks.xml')

        name = doc.getElementsByTagName("name")[0]
        print(name.firstChild.data)

        points = doc.getElementsByTagName("point")
        for point in points:
            id = point.getAttribute("id")
            name = point.getAttribute("name")
            x = point.getElementsByTagName("x")[0].firstChild.data
            y = point.getElementsByTagName("y")[0].firstChild.data
            z = point.getElementsByTagName("z")[0].firstChild.data
            #print("name: %s, x: %s, y: %s, z: %s" %
            #(name, x, y, z))

            self.landmarks.append(Landmark(id, name, x, y, z, False))

        splines = doc.getElementsByTagName("spline")

        for spline in splines:
            id = spline.getAttribute("id")
            name = spline.getAttribute("name")
            resolution = spline.getElementsByTagName("resolution")[0].firstChild.data
            splinepoints = spline.getElementsByTagName("splinepoint")
            #print (name)
            #print (resolution)
            landmarks = []
            for splinepoint in splinepoints:
                landmark = splinepoint.firstChild.data
                landmarks.append(landmark)
                #print (landmark)

            self.splines.append(Spline(id, name, resolution, landmarks, 0))

        for spline in self.splines:
            id = spline.id
            name = spline.name
            resolution = spline.resolution
            print ("spline id: %s, name: %s, resolution: %s" % (id, name, resolution))
            for landmark in spline.landmarks:
                id = landmark
                print("   landmarks id: %s" % (id))

    ### Logic ###

    def onTableCellClicked(self):
        if self.table.currentColumn() == 0:
             print(self.table.currentRow())
            # currentFid = self.table.currentRow()
            # position = [0, 0, 0]
            # self.fiducial = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
            # self.fiducial.GetNthFiducialPosition(currentFid, position)
            # print(position)
            # self.cameraFocus(position)

    def beginPlacing(self):
        if self.placingStarted == False:
            print("begin placing landmarks")
            self.begin()
            self.btnBeginPlacingLandmarks.setText("Stop Placing")
            self.placingStarted = True
        else:
            print("stop placing landmarks")
            self.stop()
            self.placingStarted = False
            self.btnBeginPlacingLandmarks.setText("Begin Placing")

    def begin(self):
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
        interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        placeModePersistence = 1
        interactionNode.SetPlaceModePersistence(placeModePersistence)
        interactionNode.SetCurrentInteractionMode(1)

    def stop(self):
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
        interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
        placeModePersistence = 1
        interactionNode.SetPlaceModePersistence(placeModePersistence)
        interactionNode.SetCurrentInteractionMode(2)
        self.getPositionsOfFiducials()

    def deleteFiducial(self):
        if self.table.currentColumn() == 0:
            item = self.table.currentItem()
            self.fidNumber = self.fiducial.GetNumberOfFiducials()
            self.fiducial = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
            for i in range(0, self.fidNumber):
                if item.text() == self.fiducial.GetNthFiducialLabel(i):
                    deleteIndex = i
            self.fiducial.RemoveMarkup(deleteIndex)
            deleteIndex = -1

            print (self.table.currentRow())
            row = (self.table.currentRow())
            self.table.removeRow(row)

    def placeFiducialAsLandmark(self, observer, event):
        print(event)
        fiducial = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
        fidNumber = fiducial.GetNumberOfFiducials()

        if (fidNumber > self.curNumberOfFids):
            print ("Fiducial added")
            slicer.modules.markups.logic().SetAllMarkupsVisibility(fiducial, 1)
            print (fidNumber)
            fiducialID = qt.QTableWidgetItem(fiducial.GetNthFiducialLabel(fidNumber - 1))

            self.table.setItem(self.selectedTableRow, 1, fiducialID)
            self.table.selectRow(self.selectedTableRow + 1)

            self.selectedTableRow += 1
            self.curNumberOfFids += 1

        if (self.selectedTableRow >= len(self.landmarks)):
            self.stop()
            self.btnBeginPlacingLandmarks.hide()


    def getPositionsOfFiducials(self):
        print ("get fiducial positions")
        fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')
        numFids = fidNode.GetNumberOfFiducials()

        for i in range(0, numFids):
            position = [0, 0, 0]
            fidNode.GetNthFiducialPosition(i, position)
            print(position)

            self.landmarks[i].x = position[0]
            self.landmarks[i].y = position[1]
            self.landmarks[i].z = position[2]

            x = qt.QTableWidgetItem(str(position[0]))
            y = qt.QTableWidgetItem(str(position[1]))
            z = qt.QTableWidgetItem(str(position[2]))

            self.table.setItem(i, 2, x)
            self.table.setItem(i, 3, y)
            self.table.setItem(i, 4, z)



    def euclDist(self, a, b):
        return numpy.linalg.norm(a-b)

    def findNeighbors(self, pointId):
        #for i in range(0, self.moulagePolys.GetNumberOfCells()):
        neighbors = vtk.vtkIdList()
        self.moulagePolys.GetCell(pointId, neighbors)

        return neighbors

    def findClosestNeighbor(self, curPointId, neighbors):

        closestNeighborId = -1
        closestDist = float("inf")

        curPoint = self.moulagePoints.GetPoint(curPointId)

        print ("curPoint: ")
        print (curPointId)
        print (curPoint)

        for i in range(0, neighbors.GetNumberOfIds()):
            neighborId = neighbors.GetId(i)

            if neighborId == curPointId:
                continue
            neighborPoint = self.moulagePoints.GetPoint(neighborId)

            a = numpy.array((curPoint[0], curPoint[1], curPoint[2]))
            b = numpy.array((neighborPoint[0], neighborPoint[1], neighborPoint[2]))

            curDist = self.euclDist(a, b)

            print ("neighbor: ")
            print (neighborId)
            print (neighborPoint)

            print (curDist)

            if curDist < closestDist:
                closestDist = curDist
                closestNeighborId = neighborId

        return closestNeighborId


    def findClosestVertexToFiducial(self, fiducialPos):

        points = self.meshPoints
        closestPointId = -1
        closestDist = float("inf")

        print ("fiducialPos: ")
        print (fiducialPos)

        for i in range(0, points.GetNumberOfPoints()):
            pointPos = [0,0,0]
            points.GetPoint(i, pointPos)

            a = numpy.array((fiducialPos[0], fiducialPos[1], fiducialPos[2]))
            b = numpy.array((pointPos[0], pointPos[1], pointPos[2]))

            curDist = self.euclDist(a, b)

            if curDist < closestDist:
                closestDist = curDist
                closestPointId = i

        return closestPointId

    def computeSpline(self, spline, startVertexID, endVertexID, startPointPosition, endPointPosition, resolution):
        print ("compute spline")
        scene = slicer.mrmlScene

        dijkstra = vtk.vtkDijkstraGraphGeodesicPath()
        dijkstra.SetInputData(self.modelNode.GetPolyData())
        dijkstra.SetStartVertex(startVertexID)
        dijkstra.SetEndVertex(endVertexID)
        dijkstra.Update()

        #compute step size in according to resolution

        vertices = dijkstra.GetOutput().GetPoints()
        numVertices = vertices.GetNumberOfPoints()
        resStepSize = float(numVertices) / (float(resolution) - 1.0)# -2 because of start and end point

        print (numVertices)
        print (resolution)
        print (resStepSize)
        equidistantIndices = []

        curStep = 0
        for i in range(0, int(resolution)):
            curStep = (i * resStepSize) - 1
            equidistantIndices.append(int(curStep + 0.5))

        #create spline
        splinePoints = []
        points = vtk.vtkPoints()
        for index in equidistantIndices:
            print ("index")
            print (index)
            print ("position")
            position = [0, 0, 0]
            vertices.GetPoint(index, position)
            print (position)
            points.InsertNextPoint(position)
            splinePoints.append(position)

        spline.points = splinePoints

        parametricSpline = vtk.vtkParametricSpline()
        parametricSpline.SetPoints(points)

        functionSource = vtk.vtkParametricFunctionSource()
        functionSource.SetParametricFunction(parametricSpline)
        functionSource.Update()

        #create model node
        splineModel = slicer.vtkMRMLModelNode()
        splineModel.SetScene(scene)
        splineModel.SetName("splineModel-%i" % 1) #todo
        splineModel.SetAndObservePolyData(functionSource.GetOutput())

        #create display node
        splineModelDisplay = slicer.vtkMRMLModelDisplayNode()
        splineModelDisplay.SetColor(1, 0, 0)
        splineModelDisplay.SetOpacity(1)
        splineModelDisplay.SetLineWidth(4)
        splineModelDisplay.SliceIntersectionVisibilityOn()

        splineModelDisplay.SetScene(scene)
        scene.AddNode(splineModelDisplay)
        splineModel.SetAndObserveDisplayNodeID(splineModelDisplay.GetID())

        # add to scene
        splineModelDisplay.GetPolyData = functionSource.GetOutput()

        scene.AddNode(splineModel)

        splineModelTransform = slicer.vtkMRMLLinearTransformNode()
        splineModelTransform.SetName("SplineModelTransform-%i" % 1) # todo

        scene.AddNode(splineModelTransform)

    def exportSpline(self, spline):
        f = open(self.exportFile, 'a')
        f.write(spline.name)
        f.write(";")
        for point in spline.points:
            f.write(str(point[0]))
            f.write(";")
            f.write(str(point[1]))
            f.write(";")
            f.write(str(point[2]))
            f.write(";")
        f.write("\n")

        f.close()
    def exportSplines(self):
        print ("export splines")
        for spline in self.splines:
            id = spline.id
            name = spline.name
            resolution = spline.resolution
            print ("spline id: %s, name: %s, resolution: %s" % (id, name, resolution))
            self.exportSpline(spline)

    def computeSplines(self):

        scene = slicer.mrmlScene

        self.modelNode = slicer.util.getNode('moulage3DFile')
        self.meshPoints = self.modelNode.GetPolyData().GetPoints()
        fidNode = slicer.mrmlScene.GetNodeByID('vtkMRMLMarkupsFiducialNode1')

        for spline in self.splines:
            id = spline.id
            name = spline.name
            resolution = spline.resolution
            print ("spline id: %s, name: %s, resolution: %s" % (id, name, resolution))
            numSplineLandmarks = len(spline.landmarks)
            for i in range(0, numSplineLandmarks):
                if ((i + 1) < numSplineLandmarks):
                    startLandmarkID = spline.landmarks[i]
                    endLandmarkID = spline.landmarks[i + 1]

                    startX = self.landmarks[int(startLandmarkID)].x
                    startY = self.landmarks[int(startLandmarkID)].y
                    startZ = self.landmarks[int(startLandmarkID)].z
                    startPosition = [startX, startY, startZ]

                    endX = self.landmarks[int(endLandmarkID)].x
                    endY = self.landmarks[int(endLandmarkID)].y
                    endZ = self.landmarks[int(endLandmarkID)].z
                    endPosition = [endX, endY, endZ]

                    print (startPosition)
                    print (endPosition)
                    startVertexID = self.findClosestVertexToFiducial(startPosition)
                    endVertexID = self.findClosestVertexToFiducial(endPosition)
                    self.computeSpline(spline, startVertexID, endVertexID, startPosition, endPosition, spline.resolution)

        #startPointId4 = self.findClosestVertexToFiducial(fiducial7Pos)
        #endPointId4 = self.findClosestVertexToFiducial(fiducial8Pos)
        #self.findShortestPath(startPointId4, endPointId4)

        '''
        scene = slicer.mrmlScene

        linePoints = vtk.vtkPoints()
        linePoints.InsertPoint(0, fiducial1Pos)
        linePoints.InsertPoint(1, fiducial2Pos)

        lineCells = vtk.vtkCellArray()
        lineCells.InsertNextCell(numPoints)
        lineCells.InsertCellPoint(0)
        lineCells.InsertCellPoint(1)

        linePoly = vtk.vtkPolyData()
        linePoly.SetPoints(linePoints)
        linePoly.SetLines(lineCells)

        # Create model node
        lineModel = slicer.vtkMRMLModelNode()
        lineModel.SetScene(scene)
        lineModel.SetName("lineModel")
        lineModel.SetAndObservePolyData(linePoly)

        # Create display node
        lineModelDisplay = slicer.vtkMRMLModelDisplayNode()
        lineModelDisplay.SetColor(0,0,1)
        lineModelDisplay.SetOpacity(1)
        lineModelDisplay.SliceIntersectionVisibilityOn()

        lineModelDisplay.SetScene(scene)
        scene.AddNode(lineModelDisplay)
        lineModel.SetAndObserveDisplayNodeID(lineModelDisplay.GetID())

        # Add to scene
        lineModelDisplay.GetPolyData = linePoly

        scene.AddNode(lineModel)

        # Create transform node
        lineModelTransform = slicer.vtkMRMLLinearTransformNode()
        lineModelTransform.SetName("LineModelTransform")

        scene.AddNode(lineModelTransform)
        '''

'''



'''