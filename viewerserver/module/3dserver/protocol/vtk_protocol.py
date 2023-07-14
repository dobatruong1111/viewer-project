from vtk.web import protocols as vtk_protocols
from wslink import register as exportRpc

import vtk
from vtkmodules.vtkCommonCore import vtkCommand

from model.colormap import CUSTOM_COLORMAP
from model.presets import *

from measurement.utils import AfterInteractorStyle
from measurement.length_measurement import LengthMeasurementPipeline, LengthMeasurementInteractorStyle
from measurement.angle_measurement import AngleMeasurementPipeline, AngleMeasurementInteractorStyle

from cropping.crop_freehand import Contour2DPipeline, CropFreehandInteractorStyle, Operation
from cropping.utils import IPWCallback

# -------------------------------------------------------------------------
# ViewManager
# -------------------------------------------------------------------------

class Dicom3D(vtk_protocols.vtkWebProtocol):
    def __init__(self):
        self._dicomDataPath = None
    
        # Pipeline
        self.colors = vtk.vtkNamedColors()
        self.reader = vtk.vtkDICOMImageReader()
        self.modifierLabelmap = vtk.vtkImageData()
        self.mapper = vtk.vtkSmartVolumeMapper()
        self.volProperty = vtk.vtkVolumeProperty()
        self.volume = vtk.vtkVolume()
        # Transfer Function
        self.color = vtk.vtkColorTransferFunction()
        self.scalarOpacity = vtk.vtkPiecewiseFunction()

        # Background Dark/Light
        self.checkLight = False

        # Cropping By Box
        self.checkBox = False
        self.boxRep = vtk.vtkBoxRepresentation()
        self.widget = vtk.vtkBoxWidget2()
        self.planes = vtk.vtkPlanes()

        # Measurement
        self.cellPicker = vtk.vtkCellPicker()
        self.afterInteractorStyle = AfterInteractorStyle()

    @property
    def dicomDataPath(self):
        return self._dicomDataPath
    
    @dicomDataPath.setter
    def dicomDataPath(self, path):
        self._dicomDataPath = path

    def colorMappingWithStandardCT(self) -> None:
        self.color.RemoveAllPoints()
        rgbPoints = CUSTOM_COLORMAP.get("STANDARD_CT").get("rgbPoints")
        for point in rgbPoints:
            self.color.AddRGBPoint(point[0], point[1], point[2], point[3])
        self.volProperty.SetColor(self.color)
    
    def setDefaultPreset(self) -> None:
        # Muscle Preset
        self.colorMappingWithStandardCT()

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

    def resetBox(self) -> None:
        # Set clipping planes outside 3D object
        planes = vtk.vtkPlanes()
        self.mapper.SetClippingPlanes(planes)
        # Set origin bounds of box
        self.widget.GetRepresentation().PlaceWidget(self.imageData.GetBounds())
        # Turn off box
        if self.checkBox:
            self.widget.Off()
            self.checkBox = False

    @exportRpc("vtk.initialize")
    def createVisualization(self):
        renderWindowInteractor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        path = self.dicomDataPath if self.dicomDataPath is not None else "./viewerserver/module/3dserver/data/Ankle"

        # Reader
        self.reader.SetDirectoryName(path)
        self.reader.Update()

        self.imageData = self.reader.GetOutput() # vtkImageData
        self.modifierLabelmap.SetExtent(self.imageData.GetExtent())
        self.modifierLabelmap.SetOrigin(self.imageData.GetOrigin())
        self.modifierLabelmap.SetSpacing(self.imageData.GetSpacing())
        self.modifierLabelmap.SetDirectionMatrix(self.imageData.GetDirectionMatrix())
        self.modifierLabelmap.AllocateScalars(self.imageData.GetScalarType(), 1)
        self.modifierLabelmap.GetPointData().GetScalars().Fill(0)

        # Mapper
        self.mapper.SetInputData(self.imageData)

        # Volume Property
        self.volProperty.ShadeOn()
        # Light
        self.volProperty.SetAmbient(0.1)
        self.volProperty.SetDiffuse(0.9)
        self.volProperty.SetSpecular(0.2)

        # Color Mapping
        self.colorMappingWithStandardCT()

        # Muscle CT: Opacity Mapping
        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        self.volProperty.SetScalarOpacity(self.scalarOpacity)

        # Volume
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volProperty)

        # Cropping By Box
        self.boxRep.GetOutlineProperty().SetColor(1, 1, 1)
        self.boxRep.SetInsideOut(True)

        self.widget.SetRepresentation(self.boxRep)
        self.widget.SetInteractor(renderWindowInteractor)
        self.widget.GetRepresentation().SetPlaceFactor(1)
        self.widget.GetRepresentation().PlaceWidget(self.reader.GetOutput().GetBounds())
        self.widget.SetEnabled(True)

        ipwcallback = IPWCallback(self.planes, self.mapper)
        self.widget.AddObserver(vtk.vtkCommand.InteractionEvent, ipwcallback)
        self.widget.Off()

        # Cropping Freehand
        self.cellPicker.AddPickList(self.volume)
        self.cellPicker.PickFromListOn()

        # Render
        renderer.AddVolume(self.volume)
        renderer.ResetCamera()

        # Render Window
        renderWindow.Render()

        # Render Window Interactor
        renderWindowInteractor.SetPicker(self.cellPicker)

        return self.resetCamera()

    @exportRpc("vtk.dicom3d.light")
    def light(self):
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        if not self.checkLight:
            renderer.SetBackground(self.colors.GetColor3d("White"))
            self.boxRep.GetOutlineProperty().SetColor(0, 0, 0)
            self.checkLight = True
        else:
            renderer.SetBackground(self.colors.GetColor3d("Black"))
            self.boxRep.GetOutlineProperty().SetColor(1, 1, 1)
            self.checkLight = False

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)
        
    @exportRpc("vtk.dicom3d.presets.bone.ct")
    def showBoneCT(self):
        renderWindow = self.getView('-1')
        self.colorMappingWithStandardCT()

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = BONE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)
      
    @exportRpc("vtk.dicom3d.presets.angio.ct")
    def showAngioCT(self):
        renderWindow = self.getView('-1')
        self.colorMappingWithStandardCT()

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = ANGIO_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("vtk.dicom3d.presets.muscle.ct")
    def showMuscleCT(self):
        renderWindow = self.getView('-1')
        self.colorMappingWithStandardCT()

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("vtk.dicom3d.presets.mip")
    def showMip(self):
        renderWindow = self.getView('-1')

        self.color.RemoveAllPoints()
        rgbPoints = MIP.get("colorMap").get("rgbPoints")
        if len(rgbPoints):
            for point in rgbPoints:
                self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MIP.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("vtk.dicom3d.length.measurement")
    def length_measurement_handle(self):
        renderWindowInteractor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        pipeline = LengthMeasurementPipeline()
        renderer.AddActor(pipeline.firstSphereActor)
        renderer.AddActor(pipeline.secondSphereActor)
        renderer.AddActor(pipeline.lineActor)
        renderer.AddActor(pipeline.textActor)

        style = LengthMeasurementInteractorStyle(pipeline, self.afterInteractorStyle)
        renderWindowInteractor.SetInteractorStyle(style)

        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("vtk.dicom3d.angle.measurement")
    def angle_measurement_handle(self):
        renderWindowInteractor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        pipeline = AngleMeasurementPipeline()
        renderer.AddActor(pipeline.firstSphereActor)
        renderer.AddActor(pipeline.secondSphereActor)
        renderer.AddActor(pipeline.thirdSphereActor)
        renderer.AddActor(pipeline.firstLineActor)
        renderer.AddActor(pipeline.secondLineActor)
        renderer.AddActor(pipeline.arcActor)
        renderer.AddActor(pipeline.textActor)

        style = AngleMeasurementInteractorStyle(pipeline, self.afterInteractorStyle)
        renderWindowInteractor.SetInteractorStyle(style)

        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("vtk.dicom3d.crop")
    def crop3d(self):
        # self.getApplication() -> vtkWebApplication()
        renderWindow = self.getView('-1')

        if not self.checkBox:
            self.widget.On()
            self.checkBox = True
        else:
            self.widget.Off()
            self.checkBox = False

        renderWindow.Render()
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("vtk.dicom3d.crop.freehand")
    def crop_freehand_handle(self):
        renderWindowInteractor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        contour2DPipeline = Contour2DPipeline()
        renderer.AddActor(contour2DPipeline.actor)
        renderer.AddActor(contour2DPipeline.actorThin)

        cropFreehandInteractorStyle = CropFreehandInteractorStyle(
            contour2DPipeline,
            self.imageData,
            self.modifierLabelmap,
            Operation.INSIDE,
            -1000,
            self.mapper,
            self.afterInteractorStyle
        )
        renderWindowInteractor.SetInteractorStyle(cropFreehandInteractorStyle)
        
        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)

    @exportRpc("vtk.camera.reset")
    def resetCamera(self):
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        # Set origin 3D object
        self.mapper.SetInputData(self.imageData)

        self.resetBox()
        self.setDefaultPreset()

        # Remove actors
        renderer.RemoveAllViewProps()
        renderer.AddVolume(self.volume)
        renderer.ResetCamera()

        renderWindow.Render()
        self.getApplication().InvalidateCache(renderWindow)

        self.getApplication().InvokeEvent(vtkCommand.UpdateEvent)
        return -1