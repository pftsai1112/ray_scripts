# Create Planning Structures

#   RayStation version: 7.0.0.19
#   Selected patient: ...

import connect
import logging

def main():

    try:
        patient = connect.get_current('Patient')
        case = connect.get_current("Case")
        examination = connect.get_current("Examination")
    except:
        logging.warning("Aww crap, No patient")
    # Temp list of sources: replace with UI user prompt
    SourceList = [ "PTV_72", "PTV_70", "PTV_64", "PTV_60", "PTV_54" ] 
    # List of PTVs to be used
    GeneratePTVs = True
    GeneratePTVEvals = True
    GenerateUnderDose = True
    GenerateUniformDose = True
    GenerateRingHD = True
    GenerateRingLD = True
    GenerateTargetRings = True
    GenerateTargetSkin = True

    PTVPrefix = "PTV_"
    PTVEvalPrefix = "PTV_Eval_"
    for index, Target in enumerate(SourceList):
        NumMids = len(SourceList)-2
        if index == 0:
            PTVName = PTVPrefix+"High"
            PTVList = [PTVName]
            PTVEvalName = PTVEvalPrefix+"High"
            PTVEvalList = [PTVEvalName]
        elif index == len(SourceList)-1:
            PTVName = PTVPrefix+"Low"
            PTVList.append(PTVName)
            PTVEvalName = PTVEvalPrefix+"Low"
            PTVEvalList.append(PTVEvalName)
        else:
            MidTargetNumber = index - 1
            PTVName = PTVPrefix+"Mid"+str(MidTargetNumber)
            PTVList.append(PTVName)
            PTVEvalName = PTVEvalPrefix+"Mid"+str(MidTargetNumber)
            PTVEvalList.append(PTVEvalName)
    TargetColors = ["Red", "Green", "Blue", "Yellow", "Orange", "Purple"]
    # Contraction in cm to be used in the definition of the skin contour
    SkinContraction = 0.5
    ##
    # Stand off inputs
    # cm gap between higher dose targets (used for OTV volumes)
    OtvStandoff = 0.3
    # cm Expansion between targets and rings
    RingStandoff = 0.2
    ThickHDRing = 1.5
    ThickLDRing = 7.0
    # Compute UnderDose Standoff
    UnderDoseStandoff = 0.4
    ## 
    # InnerAir Parameters
    # Upper Bound on the air volume to be removed from target coverage considerations
    InnerAirHU = -900

    # Underdosed Strucutures
    UnderStruct = ["Esophagus", "OpticNerve_L", "OpticNerve_R", "SpinalCord", "BrainStem"]
    # Uniform dose Structures
    UniformStruct = ["Mandible","Lips","ConstrMuscle", "Larynx"]

    if GeneratePTVs:
        for index, Target in enumerate(SourceList):
            try:
                StructureName = PTVList[index]
                retval_PTVs = case.PatientModel.RegionsOfInterest[StructureName]
                logging.warning("Structure "+StructureName+" exists.  Its geometry will be overwritten")
            except:
                retval_PTVs = case.PatientModel.CreateRoi(Name=PTVList[index], Color=TargetColors[index], Type="Ptv", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)

            with connect.CompositeAction('ROI Algebra for (PTVs)'):
                retval_PTVs.SetAlgebraExpression(
                    ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [Target],
                        'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, 
                    ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [], 
                        'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, 
                    ResultOperation="None", 
                        ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
                retval_PTVs.UpdateDerivedGeometry(Examination=examination, Algorithm="Auto")
                retval_PTVs.ExcludeFromExport = True



    # Generate the UnderDose structure
    if GenerateUnderDose:
        try: 
            retval_UnderDose = case.PatientModel.CreateRoi(Name="UnderDose", Color="0, 255, 127", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        except:
            StructureName = 'UnderDose'
            # This next line due to the fact that the ROI object index is not case specific but the name is
            case.PatientModel.RegionsOfInterest[StructureName].Name = StructureName
            retval_UnderDose = case.PatientModel.RegionsOfInterest[StructureName]
            logging.warning("Structure "+StructureName+" exists.  Its geometry will be overwritten")

        with connect.CompositeAction('ROI Algebra (UnderDose)'):
          retval_UnderDose.SetAlgebraExpression(
              ExpressionA={ 'Operation': "Union", 'SourceRoiNames': UnderStruct, 
                  'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, 
              ExpressionB={ 'Operation': "Intersection", 'SourceRoiNames': [], 
                  'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, 
              ResultOperation="None", 
                  ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
          retval_UnderDose.ExcludeFromExport = True
          retval_UnderDose.UpdateDerivedGeometry(Examination=examination, Algorithm="Auto")

  # CompositeAction ends 

    if GenerateUniformDose:
        try:
            StructureName = "UniformDose"
            retval_UniformDose = case.PatientModel.RegionsOfInterest[StructureName]
            logging.warning("Structure "+StructureName+" exists.  Its geometry will be overwritten")
        except:
            retval_UniformDose = case.PatientModel.CreateRoi(Name="UniformDose", Color="Red", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)

        with connect.CompositeAction('ROI Algebra (UniformDose)'):
          retval_UniformDose.SetAlgebraExpression(
              ExpressionA={ 'Operation': "Union", 'SourceRoiNames': UniformStruct, 
                  'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, 
              ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [], 
                  'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } },
              ResultOperation="None", 
                  ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
          retval_UniformDose.ExcludeFromExport = True
          retval_UniformDose.UpdateDerivedGeometry(Examination=examination, Algorithm="Auto")

    # Redraw the clean external volume if neccessary
    try:
        StructureName = "ExternalClean"
        retval_ExternalClean = case.PatientModel.RegionsOfInterest[StructureName]
        logging.warning("Structure "+StructureName+" exists.  Using predefined structure.")
    except:
        retval_ExternalClean = case.PatientModel.CreateRoi(Name="ExternalClean", Color="Green", Type="External", TissueName="", RbeCellTypeName=None, RoiMaterial=None)
        retval_ExternalClean.CreateExternalGeometry(Examination=examination, ThresholdLevel=None)        
        InExternalClean = case.PatientModel.RegionsOfInterest['ExternalClean']
        retval_ExternalClean.VolumeThreshold(InputRoi=InExternalClean, Examination=examination,MinVolume = 1,MaxVolume = 200000)
        retval_ExternalClean.SetAsExternal()


        

    try:
        retval_Skin = case.PatientModel.RegionsOfInterest["Skin"]
    except: 
        retval_Skin = case.PatientModel.CreateRoi(Name="Skin", Color="Blue", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)

    with connect.CompositeAction('ROI Algebra (Skin)'):
    
      retval_Skin.SetAlgebraExpression(
         ExpressionA={ 'Operation': "Union", 'SourceRoiNames': ["ExternalClean"], 'MarginSettings': {
             'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, 
         ExpressionB={'Operation': "Union", 'SourceRoiNames': ["ExternalClean"], 'MarginSettings': {
            'Type': "Contract", 'Superior': SkinContraction, 'Inferior': SkinContraction, 'Anterior': SkinContraction, 'Posterior': SkinContraction, 'Right': SkinContraction, 'Left': SkinContraction } },
         ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
      retval_Skin.UpdateDerivedGeometry(Examination=examination, Algorithm="Auto")
      retval_Skin.ExcludeFromExport = True

      # CompositeAction ends 

    # Automated build of the Air contour
    try:
        retval_AIR = case.PatientModel.RegionsOfInterest["Air"]
    except:
        retval_AIR = case.PatientModel.CreateRoi(Name="Air", Color="Green", Type="Control", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)

    retval_AIR.GrayLevelThreshold(Examination=examination, LowThreshold=-1024, HighThreshold=InnerAirHU, PetUnit="", CbctUnit=None, BoundingBox=None)


    # Use the previous Air contour to build the InnerAir volume excluding voxels outside the External 
    try:
        retval_InnerAir = case.PatientModel.RegionsOfInterest["InnerAir"]
    except:
        retval_InnerAir = case.PatientModel.CreateRoi(Name="InnerAir", Color="SaddleBrown", Type="Control", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    with connect.CompositeAction('ROI Algebra (InnerAir)'):
      retval_InnerAir.SetAlgebraExpression(
          ExpressionA={ 'Operation': "Intersection", 'SourceRoiNames': ["ExternalClean", "Air"], 
              'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } },
          ExpressionB={ 'Operation': "Union", 'SourceRoiNames': PTVList,
              'MarginSettings': { 'Type': "Expand", 'Superior': 1, 'Inferior': 1, 'Anterior': 1, 'Posterior': 1, 'Right': 1, 'Left': 1 } }, 
          ResultOperation="Intersection", 
              ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })


      retval_InnerAir.UpdateDerivedGeometry(Examination=examination, Algorithm="Auto")
      InAir=case.PatientModel.RegionsOfInterest['InnerAir']
      retval_InnerAir.VolumeThreshold(InputRoi=InAir, Examination=examination,MinVolume = 0.1,MaxVolume = 500)
      retval_InnerAir.ExcludeFromExport = True

# Set the Sources Structure for Evals
    EvalSources = ["ExternalClean"]
    EvalSubtract = ["Skin", "InnerAir"]
    if GeneratePTVEvals:
        for index, Target in enumerate(SourceList):
            EvalName = PTVEvalList[index]
            EvalSources.append(Target)  
            try: 
                retval_Evals = case.PatientModel.RegionsOfInterest[EvalName]
            except:
                retval_Evals = case.PatientModel.CreateRoi(Name=EvalName, Color=TargetColors[index], Type="Ptv", TissueName=None, RbeCellTypeName=None, RoiMaterial=None) 

            with connect.CompositeAction('Eval Creation'):
                retval_Evals.SetAlgebraExpression(
                    ExpressionA={ 'Operation': "Intersection", 'SourceRoiNames': EvalSources,
                        'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, 
                    ExpressionB={ 'Operation': "Union", 'SourceRoiNames': EvalSubtract,
                        'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, 
                    ResultOperation="Subtraction", 
                        ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
                retval_Evals.UpdateDerivedGeometry(Examination=examination, Algorithm="Auto")
            # Add this target to the delete list
            retval_Evals.ExcludeFromExport = True
            EvalSubtract.append(Target)
# Exclusion Zone
    if GenerateUnderDose:
        try:
            StructureName = "PTV_EZ"
            retval_PTVEZ = case.PatientModel.RegionsOfInterest[StructureName]
            logging.warning("Structure "+StructureName+" exists.  This will be overwritten in this examination")
        except:
            retval_PTVEZ = case.PatientModel.CreateRoi(Name="PTV_EZ", Color="255, 0, 255", Type="Ptv", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)

        with connect.CompositeAction('PTVEZ Creation'):
            retval_PTVEZ.SetAlgebraExpression(
                ExpressionA={ 'Operation': "Union", 'SourceRoiNames': UnderStruct,
                    'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } },
                ExpressionB={ 'Operation': "Union", 'SourceRoiNames': PTVList,
                    'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } },
                ResultOperation="Intersection",
                    ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
            retval_PTVEZ.UpdateDerivedGeometry(Examination=examination, Algorithm="Auto") 
            retval_PTVEZ.ExcludeFromExport = True

    # RingHD
    if GenerateRingHD:
        # First make an ExternalClean-limited expansion volume
        StructureName = "z_derived_maxhd"
        ExcludeFromExport = True
        VisualizeStructure = False
        StructColor = " 255, 0, 255"
        SourcesA = PTVList
        MarginTypeA = "Expand"
        ExpA = [ ThickHDRing, ThickHDRing, ThickHDRing, ThickHDRing, ThickHDRing, ThickHDRing ]
        OperationA = "Union"
        SourcesB = ["ExternalClean"]
        MarginTypeB = "Expand"
        ExpB = [ 0, 0, 0, 0, 0, 0 ]
        OperationB = "Union"
        MarginTypeR = "Expand"
        ExpR = [ 0, 0, 0, 0, 0, 0 ]
        OperationResult = "Intersection"
        try:
            case.PatientModel.RegionsOfInterest[StructureName]
            logging.warning("Structure "+StructureName+" exists.  This will be overwritten in this examination")
        except:
            case.PatientModel.CreateRoi(Name=StructureName, Color=StructColor, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
      
        case.PatientModel.RegionsOfInterest[StructureName].SetAlgebraExpression(
            ExpressionA={ 'Operation': OperationA, 'SourceRoiNames': SourcesA,
                   'MarginSettings': { 'Type': MarginTypeA, 'Superior': ExpA[0], 'Inferior': ExpA[1], 'Anterior': ExpA[2], 'Posterior': ExpA[3], 'Right': ExpA[4], 'Left': ExpA[5] } },
            ExpressionB={ 'Operation': OperationB, 'SourceRoiNames': SourcesB,
                   'MarginSettings': { 'Type': MarginTypeB, 'Superior': ExpB[0], 'Inferior': ExpB[0], 'Anterior': ExpB[2], 'Posterior': ExpB[3], 'Right': ExpB[4], 'Left': ExpB[5] } },
            ResultOperation=OperationResult,
                ResultMarginSettings={ 'Type': MarginTypeR, 'Superior': ExpR[0], 'Inferior': ExpR[1], 'Anterior': ExpR[2], 'Posterior': ExpR[3], 'Right': ExpR[4], 'Left': ExpR[5] })
        case.PatientModel.RegionsOfInterest[StructureName].ExcludeFromExport = ExcludeFromExport
        case.PatientModel.RegionsOfInterest[StructureName].UpdateDerivedGeometry(Examination=examination, Algorithm="Auto") 

        StructureName = "Ring_HD"
        ExcludeFromExport = True
        VisualizeStructure = False
        StructColor = " 255, 0, 255"
        SourcesA = ["z_derived_maxhd"]
        MarginTypeA = "Expand"
        ExpA = [ 0, 0, 0, 0, 0, 0 ]
        OperationA = "Union"
        SourcesB = PTVList
        MarginTypeB = "Expand"
        ExpB = [ RingStandoff, RingStandoff, RingStandoff, RingStandoff, RingStandoff, RingStandoff]
        OperationB = "Union"
        MarginTypeR = "Expand"
        ExpR = [ 0, 0, 0, 0, 0, 0 ]
        OperationResult = "Subtraction"
        try:
            case.PatientModel.RegionsOfInterest[StructureName]
            logging.warning("Structure "+StructureName+" exists.  This will be overwritten in this examination")
        except:
            case.PatientModel.CreateRoi(Name=StructureName, Color=StructColor, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
      
        case.PatientModel.RegionsOfInterest[StructureName].SetAlgebraExpression(
            ExpressionA={ 'Operation': OperationA, 'SourceRoiNames': SourcesA,
                   'MarginSettings': { 'Type': MarginTypeA, 'Superior': ExpA[0], 'Inferior': ExpA[1], 'Anterior': ExpA[2], 'Posterior': ExpA[3], 'Right': ExpA[4], 'Left': ExpA[5] } },
            ExpressionB={ 'Operation': OperationB, 'SourceRoiNames': SourcesB,
                   'MarginSettings': { 'Type': MarginTypeB, 'Superior': ExpB[0], 'Inferior': ExpB[0], 'Anterior': ExpB[2], 'Posterior': ExpB[3], 'Right': ExpB[4], 'Left': ExpB[5] } },
            ResultOperation=OperationResult,
                ResultMarginSettings={ 'Type': MarginTypeR, 'Superior': ExpR[0], 'Inferior': ExpR[1], 'Anterior': ExpR[2], 'Posterior': ExpR[3], 'Right': ExpR[4], 'Left': ExpR[5] })
        case.PatientModel.RegionsOfInterest[StructureName].ExcludeFromExport = ExcludeFromExport
        case.PatientModel.RegionsOfInterest[StructureName].UpdateDerivedGeometry(Examination=examination, Algorithm="Auto") 

if __name__ == '__main__':
    main()
