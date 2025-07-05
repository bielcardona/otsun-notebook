from dataclasses import dataclass, astuple

import FreeCAD
import Part
# from FreeCAD import App
from FreeCAD import Base
import numpy as np
import math
from itertools import product

# CONSTANT PARAMETERS
PRIMARY_FOCUS = 800  # Focal distance of the primary mirror
PRIMARY_LENGTH = 4900  # Primary mirror length
APERTURE_WIDTH = 1250  # Total width of the primary mirror
RECEIVER_DIAMETER = 15  # Outer diameter of the receiver tube
PRIMARY_GLASS_THICKNESS = 1  #
SECONDARY_GLASS_THICKNESS = 1  #
THICKNESS_GLASS_COVER = 4  #

# VARIABLE PARAMETERS

SECONDARY_FOCUS_MIN = 40
SECONDARY_FOCUS_MAX = 80
# SECONDARY_FOCUS = np.arange(40, 81, 20)  # Focal distance of the secondary mirror
HEIGHT_CYLINDER_MIN = 100
HEIGHT_CYLINDER_MAX = 250
# HEIGHT_CYLINDER = np.arange(100, 251, 50)  # Height of the integrating cylinder center
CYLINDER_DIAMETER_MIN = 35
CYLINDER_DIAMETER_MAX = 60
# CYLINDER_DIAMETER = np.arange(40, 60.1, 10)  # Diameter of the integrating cylinder
APERTURE_CYLINDER_MIN = 13.5
APERTURE_CYLINDER_MAX = 37.5
# APERTURE_CYLINDER = np.arange(13.5, 37.6, 6)  # Aperture of the integrating cylinder
ACCEPTANCE_ANGLE_MIN = 20
ACCEPTANCE_ANGLE_MAX = 60
# ACCEPTANCE_ANGLE = np.arange(20.0, 60.01, 10)  # Semi-acceptance angle of the CPC mirror
TRUNCATION_FACTOR_MIN = 0.0
TRUNCATION_FACTOR_MAX = 1.0

@dataclass
class ParametersDesign:
    secondary_focus: float
    height_cylinder: float
    cylinder_diameter: float
    aperture_cylinder: float
    acceptance_angle: float
    truncation_factor: float
    cylinder_material: bool

    @classmethod
    def random_parameters(cls) -> 'ParametersDesign':
        return ParametersDesign(
            secondary_focus = np.random.uniform(SECONDARY_FOCUS_MIN, SECONDARY_FOCUS_MAX),
            height_cylinder = np.random.uniform(HEIGHT_CYLINDER_MIN, HEIGHT_CYLINDER_MAX),
            cylinder_diameter = np.random.uniform(CYLINDER_DIAMETER_MIN, CYLINDER_DIAMETER_MAX),
            aperture_cylinder = np.random.uniform(APERTURE_CYLINDER_MIN, APERTURE_CYLINDER_MAX),
            acceptance_angle = np.random.uniform(ACCEPTANCE_ANGLE_MIN, ACCEPTANCE_ANGLE_MAX),
            truncation_factor = np.random.uniform(TRUNCATION_FACTOR_MIN, TRUNCATION_FACTOR_MAX),
            cylinder_material = np.random.choice([True, False])
        )

    def as_tuple(self) -> tuple:
        return astuple(self)


# TRUNCATION_FACTOR = np.arange(0.0, 1.01, 0.25)  # CPC truncation factor

def single_design(parameters: ParametersDesign) -> FreeCAD.Document:
    # Alias for active Document
    doc = FreeCAD.newDocument()

    p = parameters
    if p.cylinder_material:
        cylinder_material_label = 'thinfilm_reflective_SiO2_TiO2_SiO2_Ag'
    else:
        cylinder_material_label = 'Lambertian'

    #### PRIMARY #####

    # first, we determine the secondary_width and mirror_gap

    semiaperture = APERTURE_WIDTH / 2
    _angle = np.arctan(PRIMARY_FOCUS / semiaperture)
    # ray deviated due to optical errors
    s_sun = 4.65 / 2 / 1000
    s_m = 2.4529 / 2 / 1000
    s_s = 2 / 1000
    s_t = 0.2 * np.pi / 180
    s_a = 2 / 1000
    sigma = ((2 * s_sun) ** 2 + (2 * s_m) ** 2 + (2 * s_s) ** 2 + (2 * s_t) ** 2 + (2 * s_a) ** 2) ** 0.5
    _angle = _angle + sigma
    z_point = np.tan(_angle) * semiaperture
    secondary_width = 2 * (
                z_point - (PRIMARY_FOCUS - p.secondary_focus)) * semiaperture / z_point  # width of the secondary mirror

    if secondary_width > 80:
        secondary_width = 80

    mirror_gap = secondary_width + 20  # Separation space between primary mirror sections

    # create a Part object that is a Parabola in the XY plane (the parabola is infinite).
    parabola_curve_a = Part.Parabola()
    # define de Focal distance in the X axe
    parabola_curve_a.Focal = PRIMARY_FOCUS
    # create an edge from the parabola curve with the limits in the Y axe
    edge_parabola_a = Part.Edge(parabola_curve_a, -APERTURE_WIDTH / 2.0, - mirror_gap / 2.0)
    # adds a Part object type to the document and assigns the shape representation of the edge_p
    parabola_a = doc.addObject("Part::Feature", "parabola_a")
    parabola_a.Shape = edge_parabola_a

    # transformating the edge_parabola_a
    edge_parabola_a.rotate(Base.Vector(0.0, 0.0, 0.0), Base.Vector(0.0, 1.0, 0.0), -90.0)
    edge_parabola_a.rotate(Base.Vector(0.0, 0, 0.0), Base.Vector(0.0, 0.0, 1.0), +90.0)
    edge_parabola_a.translate(Base.Vector(0.0, 0.0, 0.0))
    parabola_a.Shape = edge_parabola_a

    # create an Extrusion object to extrude the edge_p
    extruded_parabola_a = doc.addObject("Part::Extrusion", "extruded_parabola_a")
    extruded_parabola_a.Label = "extruded_parabola_a(Ag_Yang)"
    # define the extrusion for the parabola
    extruded_parabola_a.Base = parabola_a
    extruded_parabola_a.Dir = (0.0, PRIMARY_LENGTH, 0.0)
    extruded_parabola_a.Solid = False
    extruded_parabola_a.TaperAngle = 0.0
    # to recalculate the whole document
    FreeCAD.ActiveDocument.recompute()

    doc.addObject('PartDesign::Body', 'Glass_P_A')
    doc.addObject('PartDesign::FeatureBase', 'Clone_A')
    doc.getObject('Clone_A').BaseFeature = extruded_parabola_a
    doc.getObject('Clone_A').Placement = extruded_parabola_a.Placement
    doc.getObject('Clone_A').setEditorMode('Placement', 0)
    doc.getObject('Glass_P_A').Group = [doc.getObject('Clone_A')]
    doc.getObject('Glass_P_A').Tip = doc.getObject('Clone_A')
    doc.getObject('Glass_P_A').newObject('PartDesign::Pad', 'Pad_A')
    doc.getObject('Pad_A').Profile = doc.getObject('Clone_A')
    doc.getObject('Pad_A').Length = PRIMARY_GLASS_THICKNESS
    doc.getObject('Glass_P_A').Label = "Glass_P_A(SiO2_Malitson)"
    doc.recompute()

    # create a Part object that is a Parabola in the XY plane (the parabola is infinite).
    parabola_curve_b = Part.Parabola()
    # define de Focal distance in the X axe
    parabola_curve_b.Focal = PRIMARY_FOCUS
    # create an edge from the parabola curve with the limits in the Y axe
    edge_parabola_b = Part.Edge(parabola_curve_b, mirror_gap / 2.0, APERTURE_WIDTH / 2.)
    # adds a Part object type to the document and assigns the shape representation of the edge_p
    parabola_b = doc.addObject("Part::Feature", "parabola_b")
    parabola_b.Shape = edge_parabola_b

    # transformating the edge_parabola_b
    edge_parabola_b.rotate(Base.Vector(0.0, 0.0, 0.0), Base.Vector(0.0, 1.0, 0.0), -90.0)
    edge_parabola_b.rotate(Base.Vector(0.0, 0, 0.0), Base.Vector(0.0, 0.0, 1.0), +90.0)
    edge_parabola_b.translate(Base.Vector(0.0, 0.0, 0.0))
    parabola_b.Shape = edge_parabola_b

    # create an Extrusion object to extrude the edge_p
    extruded_parabola_b = doc.addObject("Part::Extrusion", "extruded_parabola_b")
    extruded_parabola_b.Label = "extruded_parabola_b(Ag_Yang)"
    # define the extrusion for the parabola
    extruded_parabola_b.Base = parabola_b
    extruded_parabola_b.Dir = (0.0, PRIMARY_LENGTH, 0.0)
    extruded_parabola_b.Solid = False
    extruded_parabola_b.TaperAngle = 0.0
    # to recalculate the whole document
    FreeCAD.ActiveDocument.recompute()

    doc.addObject('PartDesign::Body', 'Glass_P_B')
    doc.addObject('PartDesign::FeatureBase', 'Clone_B')
    doc.getObject('Clone_B').BaseFeature = extruded_parabola_b
    doc.getObject('Clone_B').Placement = extruded_parabola_b.Placement
    doc.getObject('Clone_B').setEditorMode('Placement', 0)
    doc.getObject('Glass_P_B').Group = [doc.getObject('Clone_B')]
    doc.getObject('Glass_P_B').Tip = doc.getObject('Clone_B')
    doc.getObject('Glass_P_B').newObject('PartDesign::Pad', 'Pad_B')
    doc.getObject('Pad_B').Profile = doc.getObject('Clone_B')
    doc.getObject('Pad_B').Length = PRIMARY_GLASS_THICKNESS
    doc.getObject('Glass_P_B').Label = "Glass_P_B(SiO2_Malitson)"
    doc.recompute()

    #### SECONDARY ####

    # create a Part object that is a Parabola in the XY plane (the parabola is infinite).
    parabola_curve_c = Part.Parabola()
    # define de Focal distance in the X axe
    parabola_curve_c.Focal = p.secondary_focus
    # create an edge from the parabola curve with the limits in the Y axe
    edge_parabola_c = Part.Edge(parabola_curve_c, -secondary_width / 2.0, secondary_width / 2.0)
    # adds a Part object type to the document and assigns the shape representation of the edge_p
    parabola_c = doc.addObject("Part::Feature", "parabola_c")
    parabola_c.Shape = edge_parabola_c

    # transformating the edge_parabola_c
    edge_parabola_c.rotate(Base.Vector(0.0, 0.0, 0.0), Base.Vector(0.0, 1.0, 0.0), -90.0)
    edge_parabola_c.rotate(Base.Vector(0.0, 0, 0.0), Base.Vector(0.0, 0.0, 1.0), +90.0)
    edge_parabola_c.translate(Base.Vector(0.0, 0.0, PRIMARY_FOCUS - p.secondary_focus))
    parabola_c.Shape = edge_parabola_c

    # create an Extrusion object to extrude the edge_p
    extruded_parabola_c = doc.addObject("Part::Extrusion", "extruded_parabola_c")
    extruded_parabola_c.Label = "extruded_parabola_c(Ag_Yang)"
    # define the extrusion for the parabola
    extruded_parabola_c.Base = parabola_c
    extruded_parabola_c.Dir = (0.0, PRIMARY_LENGTH, 0.0)
    extruded_parabola_c.Solid = False
    extruded_parabola_c.TaperAngle = 0.0
    # to recalculate the whole document
    FreeCAD.ActiveDocument.recompute()

    doc.addObject('PartDesign::Body', 'Glass_P_C')
    doc.addObject('PartDesign::FeatureBase', 'Clone_C')
    doc.getObject('Clone_C').BaseFeature = extruded_parabola_c
    doc.getObject('Clone_C').Placement = extruded_parabola_c.Placement
    doc.getObject('Clone_C').setEditorMode('Placement', 0)
    doc.getObject('Glass_P_C').Group = [doc.getObject('Clone_C')]
    doc.getObject('Glass_P_C').Tip = doc.getObject('Clone_C')
    doc.getObject('Glass_P_C').newObject('PartDesign::Pad', 'Pad_C')
    doc.getObject('Pad_C').Profile = doc.getObject('Clone_C')
    doc.getObject('Pad_C').Length = SECONDARY_GLASS_THICKNESS
    doc.getObject('Pad_C').Reversed = 1
    doc.getObject('Glass_P_C').Label = "Glass_P_C(SiO2_Malitson)"
    doc.recompute()

    #### RECEIVER TUBE ####

    # create a generic circle for the absorber
    circle_abs = Part.makeCircle(RECEIVER_DIAMETER / 2.0, Base.Vector(0.0, 0.0, p.height_cylinder),
                                 Base.Vector(0.0, 1.0, 0.0))
    # create a FreeCAD object with Part attributes
    circle_abs_part = doc.addObject("Part::Feature", "circle_abs_part")
    # assign the circle to circle_abs_part
    circle_abs_part.Shape = circle_abs

    # create a Extrusion object for the extrusion
    tube_receiver = doc.addObject("Part::Extrusion", "tube_receiver")
    tube_receiver.Label = "tube_receiver(Abs)"
    # define the extrusion of the parabola
    tube_receiver.Base = circle_abs_part
    tube_receiver.Dir = (0.0, PRIMARY_LENGTH, 0.0)
    tube_receiver.Solid = False
    tube_receiver.TaperAngle = 0.0
    tube_receiver.Placement = Base.Placement(Base.Vector(0.0, 0, 0), Base.Rotation(Base.Vector(1.0, 0.0, 0.0), 0.0))
    # to recalculate the whole document
    FreeCAD.ActiveDocument.recompute()

    #### CPC ####

    # Inputs for the CPC
    a_width = p.aperture_cylinder  # emitter window
    angle_ = np.arcsin((a_width / 2) / (p.cylinder_diameter / 2))
    height_absorber = p.height_cylinder + (p.cylinder_diameter / 2) * np.cos(
        angle_)  # thermal absorber height from the primary mirrors
    theta_ = p.acceptance_angle * np.pi / 180  # acceptance angle for the CPC in radians
    # Parameters for geometry determination
    a = a_width / 2  # half absorber width
    a_prima = a / math.sin(theta_)  # half absorber width
    focal_distance_cpc = a * (1 + math.sin(theta_))  # CPC focal distance
    h_cpc = focal_distance_cpc * math.cos(theta_) / (math.sin(theta_) ** 2)  # CPC height without truncation
    h_cpc_t = h_cpc * p.truncation_factor  # CPC height truncated
    h_cpc_aperture = height_absorber - h_cpc_t  # height of the CPC aperture from primary mirrors
    b = a / math.tan(theta_)  # Intersection between acceptance lines

    # Algortihm to find the phi angle coordinates according to the CPC truncation.
    # The phi angle is the aperture angle of the truncated CPC.
    for phi_ in np.arange(theta_, np.pi, 1E-6):
        hi = focal_distance_cpc * math.cos(phi_ - theta_) / (math.sin(phi_ / 2) ** 2)
        if (hi < h_cpc_t):
            break

    a_cpc_t = focal_distance_cpc * math.sin(phi_ - theta_) / (
        (math.sin(phi_ / 2) ** 2)) - a  # half CPC truncated aperture

    # m and n parameters for the CPC parabolas
    n = 2 * a * math.cos(theta_)
    m = (a + a_cpc_t) * math.sin(phi_) / math.sin(phi_ - theta_)

    # --------------------------------------- CPC ------------------------------------------------------
    x_pos = a - focal_distance_cpc * math.sin(theta_)  # X placement parabola for CPC
    y_pos = focal_distance_cpc * math.cos(theta_)  # Y placement parabola for CPC
    # Create parabola CPC
    parab_cpc = Part.Parabola()
    # define de Focal distance in the X axe
    parab_cpc.Focal = focal_distance_cpc
    # create an edge from the parabola curve with the limits in the Y axe
    half_parab_cpc = Part.Edge(parab_cpc, m, n)

    # transformating the face_parabola and creating a face Part
    half_parab_cpc.rotate(Base.Vector(0.0, 0.0, 0.0), Base.Vector(0.0, 0.0, 1.0), -theta_ * 180 / np.pi)
    half_parab_cpc.rotate(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), 90)
    half_parab_cpc.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)

    half_parab_cpc.translate(Base.Vector(x_pos, 0, -y_pos))
    half_parab_cpc.translate(Base.Vector(0, 0, height_absorber))
    # Part.show(half_parab_cpc)

    # adds a Part object type to the document and assigns the shape representation of the edge_p
    parabola_cpc_a = doc.addObject("Part::Feature", "parabola_cpc_a")
    parabola_cpc_a.Shape = half_parab_cpc

    # create an Extrusion object to extrude the parabola_CPC_A
    extruded_parabola_cpc_a = doc.addObject("Part::Extrusion", "extruded_parabola_cpc_a")
    extruded_parabola_cpc_a.Label = "extruded_parabola_cpc_a(thinfilm_reflective_SiO2_TiO2_SiO2_Ag)"
    # define the extrusion for the parabola
    extruded_parabola_cpc_a.Base = parabola_cpc_a
    extruded_parabola_cpc_a.Dir = (0.0, PRIMARY_LENGTH, 0.0)
    extruded_parabola_cpc_a.Solid = (False)
    extruded_parabola_cpc_a.TaperAngle = (0.0)
    # to recalculate the whole document
    FreeCAD.ActiveDocument.recompute()

    # we create the other side of the CPC
    half_parab_cpc.rotate(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), 180)
    # adds a Part object type to the document and assigns the shape representation of the edge_p
    parabola_cpc_b = doc.addObject("Part::Feature", "parabola_cpc_b")
    parabola_cpc_b.Shape = half_parab_cpc
    # parabola_cpc_b.Placement = Base.Placement(Base.Vector(0.0, 0 ,0),Base.Rotation(Base.Vector(0.0,0.0,1.0),0.0))

    # create an Extrusion object to extrude the parabola_CPC_B
    extruded_parabola_cpc_b = doc.addObject("Part::Extrusion", "extruded_parabola_cpc_b")
    extruded_parabola_cpc_b.Label = "extruded_parabola_cpc_b(thinfilm_reflective_SiO2_TiO2_SiO2_Ag)"
    # define the extrusion for the parabola
    extruded_parabola_cpc_b.Base = parabola_cpc_b
    extruded_parabola_cpc_b.Dir = (0.0, PRIMARY_LENGTH, 0.0)
    extruded_parabola_cpc_b.Solid = (False)
    extruded_parabola_cpc_b.TaperAngle = (0.0)
    # to recalculate the whole document
    FreeCAD.ActiveDocument.recompute()

    #### CYLINDER ####

    # create a generic circle for the CYLINDER

    v1 = Base.Vector(parabola_cpc_a.Shape.BoundBox.XMax, parabola_cpc_a.Shape.BoundBox.YMin,
                     parabola_cpc_a.Shape.BoundBox.ZMin)
    v2 = Base.Vector(parabola_cpc_b.Shape.BoundBox.XMin, parabola_cpc_b.Shape.BoundBox.YMin,
                     parabola_cpc_b.Shape.BoundBox.ZMin)
    v3 = Base.Vector(0, parabola_cpc_b.Shape.BoundBox.YMin, p.height_cylinder - p.cylinder_diameter / 2.0)

    # Crear un arco usando los tres puntos
    arc = Part.Arc(v1, v3, v2)

    # Convertir el arco en un borde (edge)
    edge = arc.toShape()

    # Añadir un objeto de tipo Part al documento y asignarle el borde como su forma
    cylinder_edge = doc.addObject("Part::Feature", "cylinder_edge")
    cylinder_edge.Shape = edge

    # create a Extrusion object for the cylinder extrusion
    cylinder = doc.addObject("Part::Extrusion", "cylinder")
    cylinder.Label = "cylinder({})".format(cylinder_material_label)
    # define the extrusion of the parabola
    cylinder.Base = cylinder_edge
    cylinder.Dir = (0.0, PRIMARY_LENGTH, 0.0)
    cylinder.Solid = (False)
    cylinder.TaperAngle = (0.0)
    cylinder.Placement = Base.Placement(Base.Vector(0.0, 0, 0), Base.Rotation(Base.Vector(1.0, 0.0, 0.0), 0.0))
    # to recalculate the whole document
    FreeCAD.ActiveDocument.recompute()

    #### COVER GLASS ####

    v1 = Base.Vector(parabola_cpc_a.Shape.BoundBox.XMin, parabola_cpc_a.Shape.BoundBox.YMax,
                     parabola_cpc_a.Shape.BoundBox.ZMax)
    v2 = Base.Vector(parabola_cpc_b.Shape.BoundBox.XMax, parabola_cpc_b.Shape.BoundBox.YMax,
                     parabola_cpc_b.Shape.BoundBox.ZMax)

    glass = FreeCAD.ActiveDocument.addObject("Part::Box", "glass")
    glass.Label = "glass(BK7_Schott)"
    glass.Placement = Base.Placement(v1, Base.Rotation(Base.Vector(1.0, 0.0, 0.0), 0.0))
    glass.Height = THICKNESS_GLASS_COVER
    glass.Length = parabola_cpc_b.Shape.BoundBox.XMax - parabola_cpc_a.Shape.BoundBox.XMin
    glass.Width = PRIMARY_LENGTH

    #### Anti-Reflective layers ####

    ar_out = doc.addObject('Part::Feature', 'ar_out')
    ar_out.Shape = glass.Shape.Faces[5]
    ar_out.Label = 'ar_out(MgF2_BK7)'
    ar_in = doc.addObject('Part::Feature', 'ar_in')
    ar_in.Shape = glass.Shape.Faces[4]
    ar_in.Label = 'ar_in(MgF2_BK7)'

    # print('Aperture area = ', PRIMARY_LENGHT * APERTURE_WIDTH, 'mm2') # 6125000

    doc.recompute()
    # a = list(arg)
    # # b = round(a[5], 2)
    # # a[5] = b
    # print(a)
    # Label_drawing = "designs_set_1/design_{0}".format(a) + ".FCStd"
    # doc.saveAs(Label_drawing)
    # if face_CPC.BoundBox.ZMax + 100 < face.BoundBox.ZMin:
    #     Label_drawing = "designs_set_1/design_{0}".format(a)+".FCStd"
    #     doc.saveAs(Label_drawing)

    return doc


def random_design() -> tuple[FreeCAD.Document, ParametersDesign]:
    parameters = ParametersDesign.random_parameters()
    return single_design(parameters), parameters

