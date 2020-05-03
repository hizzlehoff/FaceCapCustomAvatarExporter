# Copyright 2020 - www.bannaflak.com
# https://github.com/hizzlehoff/FaceCapCustomAvatarExporter

# Version 0.1

# Still new to Blender, scripting feedback is welcome.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# TODO: Solve duplicate UV coordinates issue.

bl_info = {
    "name": "Face Cap Custom Avatar Exporter (.FCA)",
    "author": "Bannaflak",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "Face Cap side panel, N",
    "description": "Face Cap Side panel for exporting custom avatars (.FCA).",
    "warning": "",
    "wiki_url": "http://www.bannaflak.com/",
    "category": "Import-Export",
}

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from bpy.props import (StringProperty, FloatProperty)
import collections
from collections import namedtuple
import bmesh
import copy
import os

class CustomPropertyGroup_FaceCapExport(bpy.types.PropertyGroup):
    scale : FloatProperty(
    name = "scale",
    description="A float property",
    default = 1,
    min = 0.001,
    max = 1000.0
    )

class CUSTOM_OT_FaceCapCustomAvatarCheck(bpy.types.Operator, ExportHelper):
    bl_idname = "action.face_cap_custom_avatar_check"
    bl_label = "Export .FCA"
    bl_description = "Check selection for Face Cap custom avatar requirements and export .FCA"

    filename_ext = ".FCA"

    filter_glob: StringProperty(
        default="*.FCA",
        options={'HIDDEN'},
        maxlen=255,
    )

    # Show popup with the error string.
    def printError(self, errorString):
        self.report({'ERROR'}, errorString)

    def printReport(self, errorString):
        self.report({'INFO'}, errorString)

    # Return true of the object has children.
    def objectHasChildren(self, parent):
        if len(parent.children) > 0:
            return True
        else:
            return False

    # If it doesn't exist already add a TRIANGULATE modifier and rename it (TODO: check if it's active?).
    def addTriangulateModifier(self, context, object):
        context.view_layer.objects.active = object

        if "FaceCap_Triangulate" not in object.modifiers:
            bpy.ops.object.modifier_add(type='TRIANGULATE')
            object.modifiers[len(object.modifiers)-1].name = "FaceCap_Triangulate"

    # Remove the TRIANGULATE modifier if it exists.
    def removeTriangulateModifier(self, object):
        object.modifiers.remove(object.modifiers.get("FaceCap_Triangulate"))

    # Return a dictionary with the compatible blendshape names.
    def getCompatibleShapeKeys(self, keyBlocks):
        faceCapNames = ['browInnerUp','browDown_L','browDown_R','browOuterUp_L','browOuterUp_R','eyeLookUp_L','eyeLookUp_R','eyeLookDown_L','eyeLookDown_R','eyeLookIn_L','eyeLookIn_R','eyeLookOut_L','eyeLookOut_R','eyeBlink_L','eyeBlink_R','eyeSquint_L','eyeSquint_R','eyeWide_L','eyeWide_R','cheekPuff','cheekSquint_L','cheekSquint_R','noseSneer_L','noseSneer_R','jawOpen','jawForward','jawLeft','jawRight','mouthFunnel','mouthPucker','mouthLeft','mouthRight','mouthRollUpper','mouthRollLower','mouthShrugUpper','mouthShrugLower','mouthClose','mouthSmile_L','mouthSmile_R','mouthFrown_L','mouthFrown_R','mouthDimple_L','mouthDimple_R','mouthUpperUp_L','mouthUpperUp_R','mouthLowerDown_L','mouthLowerDown_R','mouthPress_L','mouthPress_R','mouthStretch_L','mouthStretch_R','tongueOut']
        polywinkNames = ['browInnerUp','browDownLeft','browDownRight','browOuterUpLeft','browOuterUpRight','eyeLookUpLeft','eyeLookUpRight','eyeLookDownLeft','eyeLookDownRight','eyeLookInLeft','eyeLookInRight','eyeLookOutLeft','eyeLookOutRight','eyeBlinkLeft','eyeBlinkRight','eyeSquintLeft','eyeSquintRight','eyeWideLeft','eyeWideRight','cheekPuff','cheekSquintLeft','cheekSquintRight','noseSneerLeft','noseSneerRight','jawOpen','jawForward','jawLeft','jawRight','mouthFunnel','mouthPucker','mouthLeft','mouthRight','mouthRollUpper','mouthRollLower','mouthShrugUpper','mouthShrugLower','mouthClose','mouthSmileLeft','mouthSmileRight','mouthFrownLeft','mouthFrownRight','mouthDimpleLeft','mouthDimpleRight','mouthUpperUpLeft','mouthUpperUpRight','mouthLowerDownLeft','mouthLowerDownRight','mouthPressLeft','mouthPressRight','mouthStretchLeft','mouthStretchRight','tongueOut']
        compatibleShapeKeys = {}
        for j in range(0, len(keyBlocks)):
            for i in range(0, len(faceCapNames)):
                if keyBlocks[j].name in faceCapNames[i]:
                    compatibleShapeKeys[faceCapNames[i]] = faceCapNames[i]
                elif keyBlocks[j].name in polywinkNames[i]:
                    compatibleShapeKeys[polywinkNames[i]] = faceCapNames[i]
        return compatibleShapeKeys

    def rndVal(self, value):
        value = round(value * 1000.0)/1000.0
        return str(value)

    # Export data to .FCA file.
    def exportFCA(self, outputPath, modelData, shapeKeyData):

        outputFile = open(outputPath,"w", encoding='utf-8') 

        outputFile.write('FaceCapAvatarVersion,0.1\n')
        outputFile.write('Objects,'+str(len(modelData))+'\n')

        for j in range(0,len(modelData)):

            if j == 0:
                outputFile.write('Object,BlendshapeObject,0,0,0\n')
            else:
                outputFile.write('Object,'+modelData[j].name + ',' +
                self.rndVal(modelData[j].location[0]) + ',' +
                self.rndVal(modelData[j].location[1]) + ',' +
                self.rndVal(modelData[j].location[2]) + '\n')

            outputFile.write('Vtx,' + str(len(modelData[j].vertices)) + '\n')
            for i in range(0, len(modelData[j].vertices)):
                v = modelData[j].vertices[i]
                outputFile.write( self.rndVal(v[0]) + ',' + self.rndVal(v[1]) + ',' + self.rndVal(v[2]) + '\n' )

            outputFile.write('Normals,' + str(len(modelData[j].normals)) + '\n')
            for i in range(0, len(modelData[j].vertices)):
                n = modelData[j].normals[i]
                outputFile.write( self.rndVal(n[0]) + ',' + self.rndVal(n[1]) + ',' + self.rndVal(n[2]) + '\n' )

            outputFile.write('Uvs,' + str(len(modelData[j].uvs)) + '\n')
            for i in range(0, len(modelData[j].uvs)):
                uv = modelData[j].uvs[i]
                outputFile.write(self.rndVal(uv[0]) + ',' + self.rndVal(uv[1]) + '\n')

            outputFile.write('Faces,' + str(len(modelData[j].faces)) + '\n')
            for i in range(0, len(modelData[j].faces)):
                f = modelData[j].faces[i]
                outputFile.write(
                                str(f[0]) + ':' + str(f[1]) + ':' + str(f[2]) + ',' + 
                                str(f[3]) + ':' + str(f[3]+1) + ':' + str(f[3]+2) + '\n' )

            if j == 0:
                outputFile.write('Shapes,' + str(len(shapeKeyData)) + '\n')
                for i in range (0, len(shapeKeyData)):
                    outputFile.write('ShapeName,' + shapeKeyData[i].name + '\n')
                    for h in range(0, len(shapeKeyData[i].vertices)):
                        v = shapeKeyData[i].vertices[h]
                        outputFile.write( self.rndVal(v[0]) + ',' + self.rndVal(v[1]) + ',' + self.rndVal(v[2]) + '\n' )

        outputFile.close()

    # Main
    def execute(self, context):

        # Get scale factor.
        scale = context.scene.facecap_export_props.scale

        # Get dependency graph.
        depsgraph = bpy.context.evaluated_depsgraph_get()

        # Make sure we are in object mode.
        if context.object.mode != "OBJECT":
            self.printError("Not in object mode.")
            return {"CANCELLED"}

        # Make sure just 1 object is selected.
        shapeKeyObject = bpy.context.selected_objects
        if len(shapeKeyObject) != 1:
            self.printError("Select one object with shape keys.")
            return {"CANCELLED"}
        
        shapeKeyObject = shapeKeyObject[0]

        # Make sure the children of the shapeKeyObject don't have children of their own.
        for child in shapeKeyObject.children:
            if self.objectHasChildren(child):
                self.printError("Child objects can not have children of their own.")
                return {"CANCELLED"}

        # Makes sure the selected object has shapekeys.
        if not shapeKeyObject.data.shape_keys:
            self.printError("Selected object has no shape keys.")
            return {"CANCELLED"}

        # Check for compatible shapekey names, rename Polywink convention if detected.
        compatibleShapeKeys = self.getCompatibleShapeKeys(shapeKeyObject.data.shape_keys.key_blocks)
        if not compatibleShapeKeys:
            self.printError("No compatible shape key names.")
            return {"CANCELLED"}
        
        print("FCA Export Log: "+str(len(compatibleShapeKeys))+" compatible shape keys found.")

        # Create nameTumples
        objectDataTuple = namedtuple('objectDataTuple', 'name, location, vertices, normals, uvs, faces')
        shapeKeydataTuple = namedtuple('shapeKeyDataTuple', 'name, vertices')

        # Store all the shape key data.
        shapeKeyData = []

        # Store all the shape key data.
        # Todo: Are these deltas? Are these in the same order as the bmesh?
        for key in compatibleShapeKeys.keys():
            shapeName = compatibleShapeKeys[key]
            shapeVertices = []
            for i in range(0, len(shapeKeyObject.data.shape_keys.key_blocks[key].data)):
                v = shapeKeyObject.data.shape_keys.key_blocks[key].data[i].co
                shapeVertices.append([v.x*scale,v.z*scale,-v.y*scale])
            shapeKeyData.append(shapeKeydataTuple(shapeName, copy.deepcopy(shapeVertices)))
        
        # Create List of objects to export, with the object containing shape keys first.
        objectsToExport = []
        objectsToExport.append(shapeKeyObject)
        for child in shapeKeyObject.children:
            objectsToExport.append(child)

        # Store all the object data.
        objectData = []

        # For each model:
        for i in range(0, len(objectsToExport)):

            # Check if the object is actually a mesh.
            if type(objectsToExport[i].data) != bpy.types.Mesh:
                self.printError("One or more child objects is not a mesh.")
                return {"CANCELLED"}

            # Create container for object data.
            name = objectsToExport[i].name
            location = []
            vertices = []
            normals = []
            uvs = []
            faces = []
            
            # Get object location.
            loc = bpy.data.objects[name].location
            location = [loc.x*scale, loc.z*scale, -loc.y*scale]
            
            # Add triangulatin modifier.
            self.addTriangulateModifier(context, objectsToExport[i])
            
            # Get evaluated mesh data.
            mesh = bmesh.new()
            mesh.from_object( objectsToExport[i], depsgraph )

            # Get vertices and normals.
            mesh.verts.ensure_lookup_table()
            for v in mesh.verts:
                vertices.append([v.co.x*scale, v.co.z*scale, -v.co.y*scale])
                normals.append([v.normal.x, v.normal.z, -v.normal.y])
                
            # Get active UV layer.
            uvMap = mesh.loops.layers.uv.active
            if not uvMap:
                self.printError(objectsToExport[i].name + " has no uv map.")
                return {"CANCELLED"}
            
            # Get indices for faces and UV's.
            # Todo : Clean up storing of duplicate UVs.
            uvIndex = 0
            for f in mesh.faces:
                faces.append([f.verts[0].index, f.verts[1].index, f.verts[2].index, uvIndex])
                uvIndex += 3
                for loop in f.loops:
                    uv = loop[uvMap].uv
                    uvs.append([uv.x, uv.y])

            # Free the bmesh.
            mesh.free()
            
            # Remove triangulation modifier.
            self.removeTriangulateModifier(objectsToExport[i])

            # Store object data.
            obj = objectDataTuple(name, copy.deepcopy(location), copy.deepcopy(vertices), copy.deepcopy(normals), copy.deepcopy(uvs), copy.deepcopy(faces))
            objectData.append(obj)

            # Test if mesh data is acceptable.
            if not vertices or not normals or not uvs or not faces:
                self.printError(objectsToExport[i].name + " has missing data.")
                return {"CANCELLED"}

        # Check if there is data to export.
        if not objectData or not shapeKeyData:
            self.printError("No data to export.")
            return {"CANCELLED"}
            
        # Get the export filepath.
        outputPath = self.filepath
        splitPath = os.path.split(outputPath)
        print(splitPath)
        if len(outputPath) == 1:
            self.printError("Export cancelled.")
            return {'CANCELLED'}
                
        # Export data to file.
        self.exportFCA(outputPath, objectData,shapeKeyData)

        # All done.
        self.printReport("Export completed.")
        return {"FINISHED"}

class OBJECT_PT_FaceCapCustomAvatarExporter(bpy.types.Panel):
    bl_label = "Face Cap Avatar Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Face Cap"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(context.scene.facecap_export_props, 'scale')

        row = layout.row()
        row.operator("action.face_cap_custom_avatar_check", text = "Export .FCA")

        row = layout.row()
        row.operator("wm.url_open", text="Documentation").url = "https://www.bannaflak.com/face-cap/importavatar.html"

def register():
    bpy.utils.register_class(CustomPropertyGroup_FaceCapExport)
    bpy.types.Scene.facecap_export_props = bpy.props.PointerProperty(type=CustomPropertyGroup_FaceCapExport)
    bpy.utils.register_class(CUSTOM_OT_FaceCapCustomAvatarCheck)
    bpy.utils.register_class(OBJECT_PT_FaceCapCustomAvatarExporter)

def unregister():
    del bpy.types.Scene.facecap_export_props
    bpy.utils.unregister_class(CustomPropertyGroup_FaceCapExport)
    bpy.utils.unregister_class(CUSTOM_OT_FaceCapCustomAvatarCheck)
    bpy.utils.unregister_class(OBJECT_PT_FaceCapCustomAvatarExporter)
