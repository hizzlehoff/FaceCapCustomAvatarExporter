# FaceCap Custom Avatar Exporter v0.1.2

# Todo : Error on uv ordering failure.
# Todo : Automatically copy texture to export path and rename.
# Todo : rework to check all data before writing the file.

import maya.cmds as cmds
import pymel.core as pm
import os
#import ntpath

def UpdateExportLog(logMessage):
    cmds.scrollField("errorField", edit=True, tx=logMessage)
    cmds.refresh()
    return logMessage
    
def Rnd(value):
    return (round(value*10000))/10000.0

def SetScaleToSceneUnits():
    currentUnit = cmds.currentUnit(q = True, linear=True)
    if currentUnit == 'm':
        cmds.floatField("scaleField", edit = True, value = 100.0)
    elif currentUnit == 'cm':
        cmds.floatField("scaleField", edit = True, value = 1.0)

def FaceCapExport(*args):

    faceCapAvatarVersion = "0.1"
    faceCapAvatarScale = cmds.floatField("scaleField", q=True, v=True)
    faceCapBlendShapeNames = ['browInnerUp','browDown_L','browDown_R','browOuterUp_L','browOuterUp_R','eyeLookUp_L','eyeLookUp_R','eyeLookDown_L','eyeLookDown_R','eyeLookIn_L','eyeLookIn_R','eyeLookOut_L','eyeLookOut_R','eyeBlink_L','eyeBlink_R','eyeSquint_L','eyeSquint_R','eyeWide_L','eyeWide_R','cheekPuff','cheekSquint_L','cheekSquint_R','noseSneer_L','noseSneer_R','jawOpen','jawForward','jawLeft','jawRight','mouthFunnel','mouthPucker','mouthLeft','mouthRight','mouthRollUpper','mouthRollLower','mouthShrugUpper','mouthShrugLower','mouthClose','mouthSmile_L','mouthSmile_R','mouthFrown_L','mouthFrown_R','mouthDimple_L','mouthDimple_R','mouthUpperUp_L','mouthUpperUp_R','mouthLowerDown_L','mouthLowerDown_R','mouthPress_L','mouthPress_R','mouthStretch_L','mouthStretch_R','tongueOut']
    polywinkBlendShapeNames = ['browInnerUp','browDownLeft','browDownRight','browOuterUpLeft','browOuterUpRight','eyeLookUpLeft','eyeLookUpRight','eyeLookDownLeft','eyeLookDownRight','eyeLookInLeft','eyeLookInRight','eyeLookOutLeft','eyeLookOutRight','eyeBlinkLeft','eyeBlinkRight','eyeSquintLeft','eyeSquintRight','eyeWideLeft','eyeWideRight','cheekPuff','cheekSquintLeft','cheekSquintRight','noseSneerLeft','noseSneerRight','jawOpen','jawForward','jawLeft','jawRight','mouthFunnel','mouthPucker','mouthLeft','mouthRight','mouthRollUpper','mouthRollLower','mouthShrugUpper','mouthShrugLower','mouthClose','mouthSmileLeft','mouthSmileRight','mouthFrownLeft','mouthFrownRight','mouthDimpleLeft','mouthDimpleRight','mouthUpperUpLeft','mouthUpperUpRight','mouthLowerDownLeft','mouthLowerDownRight','mouthPressLeft','mouthPressRight','mouthStretchLeft','mouthStretchRight','tongueOut']
    exportLog = ''

    selection = cmds.ls(sl=True)

    # Check sceme units
    currentUnit = cmds.currentUnit(q = True, linear=True)
    if currentUnit == 'm':
        exportLog = UpdateExportLog(exportLog+'Info: Scene is set to meters.\nInfo: Scale should be set to 100.0 approximately.\n')
    elif currentUnit == 'cm':
        exportLog = UpdateExportLog(exportLog+'Info: Scene is set to centimeters.\nInfo: Scale should be set to 1.0 approximately.\n')
    else:
        exportLog = UpdateExportLog(exportLog+'Warning: Scene units not set to meters or centimeters.\nWarning: Adjust scale to match default Avatar.\n')

    # Check if selection is a single mesh. 
    if (len(selection)!=1):
        exportLog = UpdateExportLog(exportLog+'Error: Please select the root object.\n')
        return

    # Check if selection is mesh
    my_shapes = cmds.listRelatives(shapes = True)
    if not my_shapes:
        exportLog = UpdateExportLog(exportLog+'Error: Selection does not contain a mesh.\n')
        return

    # Check if the mesh has a parent.
    parentNode = cmds.listRelatives(selection[0], p = True)
    if (parentNode):
        exportLog = UpdateExportLog(exportLog+'Error: Object must not have a parent. Did you select the root?\n')
        return

    # Check if the selected mesh has only one blendShape node.
    my_history = cmds.listHistory(selection[0])
    my_blendShape_nodes = cmds.ls( my_history, type='blendShape')
    
    if len(my_blendShape_nodes)!=1:
        exportLog = UpdateExportLog(exportLog+'Error: Root object needs one blendshape node.\n')
        return

    # List all children.
    my_children = cmds.listRelatives(selection[0], children = True, type = 'transform')
    
    # If children have rotation, free it.
    if my_children:
        for child in my_children:
            cmds.makeIdentity(child, apply = True, translate = False, rotate = True, scale = True)

    # Check if mesh has a single material.
    cmds.select(selection[0])
    pm.hyperShade(shaderNetworksSelectMaterialNodes=True)
    my_materials = cmds.ls(sl=True)
    if len(my_materials)!=1:
        exportLog = UpdateExportLog(exportLog+'Warning: FaceCap Custom avatar can have only 1 material.\n')

    # Check for compatible blendshape naming and reset all blendshape nodes to 0.
    my_blendShape_names = cmds.listAttr(my_blendShape_nodes[0]+'.w', m=True)
    compatibleBlendShapeNames = []
    
    for shapeName in my_blendShape_names:
        cmds.setAttr(my_blendShape_nodes[0]+"."+shapeName,0)
        if shapeName in faceCapBlendShapeNames or shapeName in polywinkBlendShapeNames:
            compatibleBlendShapeNames.append(shapeName)
        else:
            exportLog = UpdateExportLog(exportLog+('Warning: the name for blendshape ' + shapeName + ' is not compatible with FaceCap.\n'))
            
    if (len(compatibleBlendShapeNames)==0):
        exportLog = UpdateExportLog(exportLog+'Error: No blendshapes with compatible naming found.\n')
        return
    else:
        exportLog = UpdateExportLog(exportLog+('Info: Found '+str(len(compatibleBlendShapeNames))+' blendshapes with compatible naming.\n'))

    # Get the output file
    faceCapFilter = "*.FCA"
    exportPath = cmds.fileDialog2(fileFilter = faceCapFilter, caption = 'Pick export file *.FCA', fileMode = 0)
    if not exportPath:
        exportLog = UpdateExportLog(exportLog + 'Export canceled.\n')
        return        

    # Create list of objects containing meshes to export
    exportList = [] 
    exportListLog = str(selection[0])
    exportList.append(selection[0])

    if my_children:
        for child in my_children:
            my_shapes = cmds.listRelatives(child, shapes = True)
            if len(my_shapes)!=0:
                exportListLog += ','+str(child)
                exportList.append(child)

    exportLog = UpdateExportLog(exportLog+('Exporting: '+exportListLog+'.\n'))

    # Open a file
    file1 = open(exportPath[0],"w")
 
    # Write file header and version
    file1.write("FaceCapAvatarVersion,"+faceCapAvatarVersion+"\n")

    # Write amount of objects
    file1.write("Objects,"+str(len(exportList))+"\n")

    # Tell user to wait
    exportLog = UpdateExportLog(exportLog+'\nPlease wait')
    cmds.refresh()

    # Get frozen pivot offset for the root.
    rootOffset = cmds.xform(selection[0], sp = True, q=True, ws=True)

    # Export objects
    for objectIndex in range (0, len(exportList)):

        # Get local translation for object
        tx = Rnd((cmds.getAttr(str(exportList[objectIndex])+'.tx')- rootOffset[0]) * faceCapAvatarScale)
        ty = Rnd((cmds.getAttr(str(exportList[objectIndex])+'.ty')- rootOffset[1]) * faceCapAvatarScale)
        tz = Rnd((cmds.getAttr(str(exportList[objectIndex])+'.tz')- rootOffset[2]) * faceCapAvatarScale)

        # Write object header and position
        if objectIndex==0:
            file1.write('Object,BlendshapeObject,0,0,0\n')
        else:
            file1.write('Object,'+str(exportList[objectIndex]).strip()+','+str(tx)+','+str(ty)+','+str(tz)+'\n')
            
        # Triangulate mesh
        cmds.select(exportList[objectIndex])
        triangulationNode = cmds.polyTriangulate()
    
        # Store mesh details
        cmds.select(exportList[objectIndex])
        vtxCount = cmds.polyEvaluate(v=True)
        uvCount = cmds.polyEvaluate(uv=True)
        faceCount = cmds.polyEvaluate(f=True)
        shapeCount = len(compatibleBlendShapeNames)
        
        # Get frozen pivot offset
        vtxOffset = cmds.xform(exportList[objectIndex], sp = True, q=True, ws=True)

        # Write vertex data
        file1.write("Vtx,"+str(vtxCount)+"\n")
        for i in range(0, vtxCount):
            position = cmds.xform(exportList[objectIndex]+".vtx["+str(i)+"]",q=True,objectSpace=True,t=True)
            if objectIndex==0:
                position[0] -= vtxOffset[0]
                position[1] -= vtxOffset[1]
                position[2] -= vtxOffset[2]
            file1.write(str(Rnd(faceCapAvatarScale*position[0]))+","+str(Rnd(faceCapAvatarScale*position[1]))+","+str(Rnd(faceCapAvatarScale*position[2]))+"\n")
    
        exportLog = UpdateExportLog(exportLog + '.')

        # Write normal data
        file1.write("Normals,"+str(vtxCount)+"\n")
        for i in range(0, vtxCount):
            normalsX = cmds.polyNormalPerVertex(exportList[objectIndex]+".vtx["+str(i)+"]",q = True, x = True)
            normalsY = cmds.polyNormalPerVertex(exportList[objectIndex]+".vtx["+str(i)+"]",q = True, y = True)
            normalsZ = cmds.polyNormalPerVertex(exportList[objectIndex]+".vtx["+str(i)+"]",q = True, z = True)
            if normalsX and normalsY and normalsZ:
                normalX = sum(normalsX)/len(normalsX)
                normalY = sum(normalsY)/len(normalsY)
                normalZ = sum(normalsZ)/len(normalsZ)
                file1.write(str(Rnd(normalX))+","+str(Rnd(normalY))+","+str(Rnd(normalZ))+"\n")
            else:
                normalX = 0
                normalY = 1
                normalZ = 0
                file1.write(str(Rnd(normalX))+","+str(Rnd(normalY))+","+str(Rnd(normalZ))+"\n")
    
        exportLog = UpdateExportLog(exportLog + '.')

        # Write uv data
        file1.write("Uvs,"+str(uvCount)+"\n")
        for i in range(0, uvCount):
            cmds.select(exportList[objectIndex]+".map["+str(i)+"]")
            uvs = cmds.polyEditUV(q=True)
            file1.write(str(Rnd(uvs[0]))+","+str(Rnd(uvs[1]))+"\n")
    
        exportLog = UpdateExportLog(exportLog + '.')

        # Write face data, uv indices need to be re-ordered.
        file1.write("Faces,"+str(faceCount)+"\n")
        for f in range(0, faceCount):
    
            orderedVtxIndices = cmds.polyInfo( (exportList[objectIndex]+".f["+str(f)+"]"), fv=True)[0]
            orderedVtxIndices = orderedVtxIndices.split()
            orderedVtxIndices = [int(i) for i in orderedVtxIndices[2:]]

            uvIndices = maya.cmds.polyListComponentConversion( (exportList[objectIndex]+".f["+str(f)+"]"), fromFace=True, toUV=True)
            if uvIndices:
                uvIndices = maya.cmds.filterExpand(uvIndices,sm=35, ex=True)
                uvIndices = [int(i.split("map")[-1].strip("[]")) for i in uvIndices]
            else:
                exportLog = UpdateExportLog(exportLog+'\nError: Model needs to have 1 uv channel.'+exportPath[0]+'\n')
                exportLog = UpdateExportLog(exportLog+'\nError: output file is incomplete.'+exportPath[0]+'\n\n')
                sys.exit()
                
            tmpDict = {}
            for t in uvIndices:
                vtxFromUv = maya.cmds.polyListComponentConversion( (exportList[objectIndex]+".map["+str(t)+"]"), fromUV=True, toVertex=True)
                index = int(vtxFromUv[0].split("[")[-1].split("]")[0])
                tmpDict[index] = t
            
            orderedPolyUvs=[]
            for vtx in orderedVtxIndices:
                orderedPolyUvs.append(tmpDict[vtx])
            
            file1.write(str(orderedVtxIndices[0])+":"+str(orderedVtxIndices[1])+":"+str(orderedVtxIndices[2])+","+str(orderedPolyUvs[0])+":"+str(orderedPolyUvs[1])+":"+str(orderedPolyUvs[2]))
            file1.write("\n")
            
        exportLog = UpdateExportLog(exportLog + '.')

        # Write shape data
        if objectIndex==0:
            file1.write("Shapes,"+str(shapeCount)+"\n")
            
            for i in range(0,shapeCount):
                # Change polywink blendshape naming to FaceCap naming
                outputShapeName = compatibleBlendShapeNames[i]
                if 'Left' in outputShapeName:
                    outputShapeName = outputShapeName.replace('Left','_L')
                elif 'Right' in outputShapeName:
                    outputShapeName = outputShapeName.replace('Right','_R')

                file1.write("ShapeName,"+outputShapeName+"\n")
                cmds.setAttr(my_blendShape_nodes[0]+"."+compatibleBlendShapeNames[i],1)
        
                for j in range(0, vtxCount):
                    position = cmds.xform(exportList[objectIndex]+".vtx["+str(j)+"]",q=True,objectSpace=True,t=True)
                    position[0] -= vtxOffset[0]
                    position[1] -= vtxOffset[1]
                    position[2] -= vtxOffset[2]
                    file1.write(str(Rnd(faceCapAvatarScale*position[0]))+","+str(Rnd(faceCapAvatarScale*position[1]))+","+str(Rnd(faceCapAvatarScale*position[2]))+"\n")
        
                cmds.setAttr(my_blendShape_nodes[0]+"."+compatibleBlendShapeNames[i],0)

            exportLog = UpdateExportLog(exportLog + '.')

        # Remove triangulation mode
        cmds.delete(triangulationNode)

    # Close file
    file1.close()

    cmds.select(selection[0])
    exportLog = UpdateExportLog(exportLog+'\nResult: '+exportPath[0]+'\n')
    exportLog = UpdateExportLog(exportLog+'Finished.\n')

def OpenDocumentation(*args):
    cmds.launch(web="http://www.bannaflak.com/face-cap/importavatar.html")

def FaceCapCustomAvatarExportWindow():

    if cmds.window("FaceCapCustomAvatarExportWindow", exists = True):
        cmds.deleteUI("FaceCapCustomAvatarExportWindow")
    
    window = cmds.window("FaceCapCustomAvatarExportWindow", title="FaceCap Custom Avatar Exporter.", iconName='FaceCap', widthHeight=(400, 300), sizeable=False )
    cmds.window("FaceCapCustomAvatarExportWindow", e=True, w=400, h=300)
    
    cmds.columnLayout( adjustableColumn=True)

    cmds.rowLayout( numberOfColumns=2, columnWidth2=(200,200), adjustableColumn=2)
    cmds.text('Scale')
    cmds.floatField("scaleField", value=100.0)
    cmds.setParent( '..' )

    cmds.separator(height = 10)

    cmds.rowLayout( numberOfColumns=1, adjustableColumn=1)
    cmds.button( label='Export', command=FaceCapExport)
    cmds.setParent( '..' )
    
    cmds.separator(height = 10)

    cmds.rowLayout()
    cmds.scrollField("errorField", w=400, h=160, editable = False, tx="Validation log.", wordWrap = True)
    cmds.setParent( '..' )

    cmds.separator(height = 10)
    
    cmds.rowLayout( numberOfColumns=1, adjustableColumn=1)
    cmds.button( label='Documentation', command=OpenDocumentation)
    cmds.setParent( '..' )

    cmds.showWindow( window )
    
    SetScaleToSceneUnits()
    
FaceCapCustomAvatarExportWindow()