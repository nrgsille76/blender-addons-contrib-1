# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# Script copyright (C) Bob Holcomb
# Contributors: Bob Holcomb, Richard L?rk?ng, Damien McGinnes,
# Campbell Barton, Mario Lapin, Dominique Lorre, Andreas Atteneder

import os
import time
import struct
import bpy
import mathutils
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

BOUNDS_3DS = []


######################################################
# Data Structures
######################################################

#Some of the chunks that we will see
#----- Primary Chunk, at the beginning of each file
PRIMARY = 0x4D4D

#------ Main Chunks
OBJECTINFO = 0x3D3D  # This gives the version of the mesh and is found right before the material and object information
VERSION = 0x0002  # This gives the version of the .3ds file
EDITKEYFRAME = 0xB000  # This is the header for all of the key frame info

#------ Data Chunks, used for various attributes
PERCENTAGE_SHORT = 0x30
PERCENTAGE_FLOAT = 0x31

#------ sub defines of OBJECTINFO
MATERIAL = 0xAFFF  # This stored the texture info
OBJECT = 0x4000  # This stores the faces, vertices, etc...

#>------ sub defines of MATERIAL
#------ sub defines of MATERIAL_BLOCK
MAT_NAME = 0xA000  # This holds the material name
MAT_AMBIENT = 0xA010  # Ambient color of the object/material
MAT_DIFFUSE = 0xA020  # This holds the color of the object/material
MAT_SPECULAR = 0xA030  # Specular color of the object/material
MAT_SHINESS = 0xA040  # Roughness of the object/material (percent)
MAT_SHIN2 = 0xA041  # Shininess of the object/material (percent)
MAT_SHIN3 = 0xA042  # Reflection of the object/material (percent)
MAT_TRANSPARENCY = 0xA050  # Transparency value of material (percent)
MAT_SELF_ILLUM = 0xA080  # Self Illumination value of material
MAT_WIRE = 0xA085  # Only render's wireframe

MAT_TEXTURE_MAP = 0xA200  # This is a header for a new texture map
MAT_SPECULAR_MAP = 0xA204  # This is a header for a new specular map
MAT_OPACITY_MAP = 0xA210  # This is a header for a new opacity map
MAT_REFLECTION_MAP = 0xA220  # This is a header for a new reflection map
MAT_BUMP_MAP = 0xA230  # This is a header for a new bump map
MAT_BUMP_PERCENT = 0xA252  # Normalmap strength (percent)
MAT_TEX2_MAP = 0xA33A  # This is a header for a secondary texture
MAT_SHIN_MAP = 0xA33C  # This is a header for a new roughness map
MAT_SELFI_MAP = 0xA33D  # This is a header for a new emission map
MAT_MAP_FILEPATH = 0xA300  # This holds the file name of the texture

MAT_MAP_TILING = 0xa351   # 2nd bit (from LSB) is mirror UV flag
MAT_MAP_USCALE = 0xA354   # U axis scaling
MAT_MAP_VSCALE = 0xA356   # V axis scaling
MAT_MAP_UOFFSET = 0xA358  # U axis offset
MAT_MAP_VOFFSET = 0xA35A  # V axis offset
MAT_MAP_ANG = 0xA35C      # UV rotation around the z-axis in rad

MAT_FLOAT_COLOR = 0x0010  # color defined as 3 floats
MAT_24BIT_COLOR = 0x0011  # color defined as 3 bytes

#>------ sub defines of OBJECT
OBJECT_MESH = 0x4100  # This lets us know that we are reading a new object
OBJECT_LIGHT = 0x4600  # This lets un know we are reading a light object
OBJECT_LIGHT_SPOT = 0x4610  # The light is a spotloght.
OBJECT_LIGHT_OFF = 0x4620  # The light off.
OBJECT_LIGHT_ATTENUATE = 0x4625
OBJECT_LIGHT_RAYSHADE = 0x4627
OBJECT_LIGHT_SHADOWED = 0x4630
OBJECT_LIGHT_LOCAL_SHADOW = 0x4640
OBJECT_LIGHT_LOCAL_SHADOW2 = 0x4641
OBJECT_LIGHT_SEE_CONE = 0x4650
OBJECT_LIGHT_SPOT_RECTANGULAR = 0x4651
OBJECT_LIGHT_SPOT_OVERSHOOT = 0x4652
OBJECT_LIGHT_SPOT_PROJECTOR = 0x4653
OBJECT_LIGHT_EXCLUDE = 0x4654
OBJECT_LIGHT_RANGE = 0x4655
OBJECT_LIGHT_ROLL = 0x4656
OBJECT_LIGHT_SPOT_ASPECT = 0x4657
OBJECT_LIGHT_RAY_BIAS = 0x4658
OBJECT_LIGHT_INNER_RANGE = 0x4659
OBJECT_LIGHT_OUTER_RANGE = 0x465A
OBJECT_LIGHT_MULTIPLIER = 0x465B
OBJECT_LIGHT_AMBIENT_LIGHT = 0x4680

OBJECT_CAMERA = 0x4700  # This lets un know we are reading a camera object

#>------ sub defines of CAMERA
OBJECT_CAM_RANGES = 0x4720  # The camera range values

#>------ sub defines of OBJECT_MESH
OBJECT_VERTICES = 0x4110  # The objects vertices
OBJECT_FACES = 0x4120  # The objects faces
OBJECT_MATERIAL = 0x4130  # This is found if the object has a material, either texture map or color
OBJECT_UV = 0x4140  # The UV texture coordinates
OBJECT_TRANS_MATRIX = 0x4160  # The Object Matrix

#>------ sub defines of EDITKEYFRAME
KFDATA_AMBIENT = 0xB001
KFDATA_OBJECT = 0xB002
KFDATA_CAMERA = 0xB003
KFDATA_TARGET = 0xB004
KFDATA_LIGHT = 0xB005
KFDATA_L_TARGET = 0xB006
KFDATA_SPOTLIGHT = 0xB007
KFDATA_KFSEG = 0xB008
# KFDATA_CURTIME = 0xB009
# KFDATA_KFHDR = 0xB00A
#>------ sub defines of ED_KEY_OBJECT_NODE
EK_OB_NODE_HEADER = 0xB010
EK_OB_INSTANCE_NAME = 0xB011
# EK_OB_PRESCALE = 0xB012
EK_OB_PIVOT = 0xB013
# EK_OB_BOUNDBOX =   0xB014
# EK_OB_MORPH_SMOOTH = 0xB015
EK_OB_POSITION_TRACK = 0xB020
EK_OB_ROTATION_TRACK = 0xB021
EK_OB_SCALE_TRACK = 0xB022
# EK_OB_CAMERA_FOV_TRACK = 0xB023
# EK_OB_CAMERA_ROLL_TRACK = 0xB024
EK_OB_COLOR_TRACK = 0xB025
# EK_OB_MORPH_TRACK = 0xB026
# EK_OB_HOTSPOT_TRACK = 0xB027
# EK_OB_FALLOF_TRACK = 0xB028
# EK_OB_HIDE_TRACK = 0xB029
# EK_OB_NODE_ID = 0xB030

ROOT_OBJECT = 0xFFFF

global scn
scn = None

object_dictionary = {}
object_matrix = {}


class Chunk:
    __slots__ = (
        "ID",
        "length",
        "bytes_read",
    )
    # we don't read in the bytes_read, we compute that
    binary_format = "<HI"

    def __init__(self):
        self.ID = 0
        self.length = 0
        self.bytes_read = 0

    def dump(self):
        print('ID: ', self.ID)
        print('ID in hex: ', hex(self.ID))
        print('length: ', self.length)
        print('bytes_read: ', self.bytes_read)


def read_chunk(file, chunk):
    temp_data = file.read(struct.calcsize(chunk.binary_format))
    data = struct.unpack(chunk.binary_format, temp_data)
    chunk.ID = data[0]
    chunk.length = data[1]
    #update the bytes read function
    chunk.bytes_read = 6

    #if debugging
    #chunk.dump()


def read_string(file):
    #read in the characters till we get a null character
    s = []
    while True:
        c = file.read(1)
        if c == b'\x00':
            break
        s.append(c)
        # print('string: ', s)

    # Remove the null character from the string
    # print("read string", s)
    return str(b''.join(s), "utf-8", "replace"), len(s) + 1

######################################################
# IMPORT
######################################################


def process_next_object_chunk(file, previous_chunk):
    new_chunk = Chunk()

    while (previous_chunk.bytes_read < previous_chunk.length):
        #read the next chunk
        read_chunk(file, new_chunk)


def skip_to_end(file, skip_chunk):
    buffer_size = skip_chunk.length - skip_chunk.bytes_read
    binary_format = "%ic" % buffer_size
    file.read(struct.calcsize(binary_format))
    skip_chunk.bytes_read += buffer_size


def add_texture_to_material(image, scale, offset, angle, extension, contextWrapper, alphaflag, mapto):
    shader = contextWrapper.node_principled_bsdf
    nodetree = contextWrapper.material.node_tree
    nodes = nodetree.nodes
    links = nodetree.links

    if mapto == 'COLOR':
        mixer = nodes.new(type='ShaderNodeMixRGB')
        mixer.label = "Mixer"
        mixer.inputs['Color2'].default_value = (0,0,0,1)
        contextWrapper._grid_to_location(0,1, dst_node=mixer, ref_node=shader)
        img_wrap = contextWrapper.base_color_texture
        links.new(img_wrap.node_image.outputs['Color'], mixer.inputs['Color1'])
        links.new(mixer.outputs["Color"], shader.inputs['Base Color'])
    elif mapto == 'SPECULARITY':
        img_wrap = contextWrapper.specular_texture
    elif mapto == 'ALPHA':
        img_wrap = contextWrapper.alpha_texture
    elif mapto == 'METALLIC':
        img_wrap = contextWrapper.metallic_texture
    elif mapto == 'ROUGHNESS':
        img_wrap = contextWrapper.roughness_texture
    elif mapto == 'EMISSION':
        img_wrap = contextWrapper.emission_color_texture
    elif mapto == 'NORMAL':
        img_wrap = contextWrapper.normalmap_texture
    elif mapto == 'TEXTURE':
        img_wrap = nodes.new(type='ShaderNodeTexImage')
        img_wrap.label = image.name
        contextWrapper._grid_to_location(-1,2, dst_node=img_wrap, ref_node=shader)
        for node in nodes:
            if node.label == 'Mixer':
                links.new(img_wrap.outputs['Color'], node.inputs['Color2'])
        if shader.inputs['Base Color'].is_linked == False:
            links.new(img_wrap.outputs['Color'], shader.inputs['Base Color'])

    img_wrap.image = image
    img_wrap.extension = 'REPEAT'
    
    if mapto != 'TEXTURE':
        img_wrap.scale = scale
        img_wrap.translation = offset
        img_wrap.rotation[2] = angle

    if extension == 'mirror':
        # 3DS mirror flag can be emulated by these settings (at least so it seems)
        # TODO: bring back mirror
        pass
        # texture.repeat_x = texture.repeat_y = 2
        # texture.use_mirror_x = texture.use_mirror_y = True
    elif extension == 'decal':
        # 3DS' decal mode maps best to Blenders EXTEND
        img_wrap.extension = 'EXTEND'
    elif extension == 'noWrap':
        img_wrap.extension = 'CLIP'
    if alphaflag == 'alpha':
        links.new(img_wrap.node_image.outputs['Alpha'], img_wrap.socket_dst)


def process_next_chunk(context, file, previous_chunk, importedObjects, IMAGE_SEARCH):
    from bpy_extras.image_utils import load_image

    contextObName = None
    contextLamp = None
    contextMaterial = None
    contextWrapper = None
    contextMatrix = None
    contextMesh_vertls = None
    contextMesh_facels = None
    contextMeshMaterials = []
    contextMeshUV = None

    TEXTURE_DICT = {}
    MATDICT = {}

    # Localspace variable names, faster.
    SZ_FLOAT = struct.calcsize('f')
    SZ_2FLOAT = struct.calcsize('2f')
    SZ_3FLOAT = struct.calcsize('3f')
    SZ_4FLOAT = struct.calcsize('4f')
    SZ_U_SHORT = struct.calcsize('H')
    SZ_4U_SHORT = struct.calcsize('4H')
    SZ_4x3MAT = struct.calcsize('ffffffffffff')

    object_list = []  # for hierarchy
    object_parent = []  # index of parent in hierarchy, 0xFFFF = no parent
    pivot_list = []  # pivots with hierarchy handling

    def putContextMesh(context, myContextMesh_vertls, myContextMesh_facels, myContextMeshMaterials):
        bmesh = bpy.data.meshes.new(contextObName)

        if myContextMesh_facels is None:
            myContextMesh_facels = []

        if myContextMesh_vertls:

            bmesh.vertices.add(len(myContextMesh_vertls) // 3)
            bmesh.vertices.foreach_set("co", myContextMesh_vertls)

            nbr_faces = len(myContextMesh_facels)
            bmesh.polygons.add(nbr_faces)
            bmesh.loops.add(nbr_faces * 3)
            eekadoodle_faces = []
            for v1, v2, v3 in myContextMesh_facels:
                eekadoodle_faces.extend((v3, v1, v2) if v3 == 0 else (v1, v2, v3))
            bmesh.polygons.foreach_set("loop_start", range(0, nbr_faces * 3, 3))
            bmesh.polygons.foreach_set("loop_total", (3,) * nbr_faces)
            bmesh.loops.foreach_set("vertex_index", eekadoodle_faces)

            if bmesh.polygons and contextMeshUV:
                bmesh.uv_layers.new()
                uv_faces = bmesh.uv_layers.active.data[:]
            else:
                uv_faces = None

            for mat_idx, (matName, faces) in enumerate(myContextMeshMaterials):
                if matName is None:
                    bmat = None
                else:
                    bmat = MATDICT.get(matName)
                    # in rare cases no materials defined.
                    if bmat:
                        img = TEXTURE_DICT.get(bmat.name)
                    else:
                        print("    warning: material %r not defined!" % matName)
                        bmat = MATDICT[matName] = bpy.data.materials.new(matName)
                        img = None

                bmesh.materials.append(bmat)  # can be None

                if uv_faces  and img:
                    for fidx in faces:
                        bmesh.polygons[fidx].material_index = mat_idx
                        # TODO: How to restore this?
                        # uv_faces[fidx].image = img
                else:
                    for fidx in faces:
                        bmesh.polygons[fidx].material_index = mat_idx

            if uv_faces:
                uvl = bmesh.uv_layers.active.data[:]
                for fidx, pl in enumerate(bmesh.polygons):
                    face = myContextMesh_facels[fidx]
                    v1, v2, v3 = face

                    # eekadoodle
                    if v3 == 0:
                        v1, v2, v3 = v3, v1, v2

                    uvl[pl.loop_start].uv = contextMeshUV[v1 * 2: (v1 * 2) + 2]
                    uvl[pl.loop_start + 1].uv = contextMeshUV[v2 * 2: (v2 * 2) + 2]
                    uvl[pl.loop_start + 2].uv = contextMeshUV[v3 * 2: (v3 * 2) + 2]
                    # always a tri

        bmesh.validate()
        bmesh.update()

        ob = bpy.data.objects.new(contextObName, bmesh)
        object_dictionary[contextObName] = ob
        context.view_layer.active_layer_collection.collection.objects.link(ob)
        importedObjects.append(ob)

        if contextMatrix:
            ob.matrix_local = contextMatrix
            object_matrix[ob] = contextMatrix.copy()

    #a spare chunk
    new_chunk = Chunk()
    temp_chunk = Chunk()

    CreateBlenderObject = False

    def read_float_color(temp_chunk):
        temp_data = file.read(SZ_3FLOAT)
        temp_chunk.bytes_read += SZ_3FLOAT
        return [float(col) for col in struct.unpack('<3f', temp_data)]

    def read_float(temp_chunk):
        temp_data = file.read(SZ_FLOAT)
        temp_chunk.bytes_read += SZ_FLOAT
        return struct.unpack('<f', temp_data)[0]

    def read_short(temp_chunk):
        temp_data = file.read(SZ_U_SHORT)
        temp_chunk.bytes_read += SZ_U_SHORT
        return struct.unpack('<H', temp_data)[0]

    def read_byte_color(temp_chunk):
        temp_data = file.read(struct.calcsize('3B'))
        temp_chunk.bytes_read += 3
        return [float(col) / 255 for col in struct.unpack('<3B', temp_data)]

    def read_texture(new_chunk, temp_chunk, name, mapto):
        u_scale, v_scale, u_offset, v_offset, angle = 1.0, 1.0, 0.0, 0.0, 0.0
        contextWrapper.use_nodes = True
        extension = 'wrap'
        alphaflag = False
        
        while (new_chunk.bytes_read < new_chunk.length):
            read_chunk(file, temp_chunk)

            if temp_chunk.ID == MAT_MAP_FILEPATH:
                texture_name, read_str_len = read_string(file)

                img = TEXTURE_DICT[contextMaterial.name] = load_image(texture_name, dirname, recursive=IMAGE_SEARCH)
                temp_chunk.bytes_read += read_str_len  # plus one for the null character that gets removed

            elif temp_chunk.ID == MAT_MAP_USCALE:
                u_scale = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_VSCALE:
                v_scale = read_float(temp_chunk)

            elif temp_chunk.ID == MAT_MAP_UOFFSET:
                u_offset = read_float(temp_chunk)
            elif temp_chunk.ID == MAT_MAP_VOFFSET:
                v_offset = read_float(temp_chunk)

            elif temp_chunk.ID == MAT_MAP_TILING:
                tiling = read_short(temp_chunk)
                if tiling & 0x1:
                    extension = 'decal'
                elif tiling & 0x2:
                    extension = 'mirror'
                elif tiling & 0x8:
                    extension = 'invert'
                elif tiling & 0x10:
                    extension = 'noWrap'
                elif tiling & 0x20:
                    alphaflag = 'sat'
                elif tiling & 0x40:
                    alphaflag = 'alpha'
                elif tiling & 0x80:
                    tintflag = 'tint'
                elif tiling & 0x100:
                    tintflag = 'noAlpha'
                elif tiling & 0x200:
                    tintflag = 'RGBtint'

            elif temp_chunk.ID == MAT_MAP_ANG:
                angle = read_float(temp_chunk)
                print("\nwarning: UV angle mapped to z-rotation")

            skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        # add the map to the material in the right channel
        if img:
            add_texture_to_material(img, (u_scale, v_scale, 1),
                                    (u_offset, v_offset, 0), angle, extension, contextWrapper, alphaflag, mapto)

    dirname = os.path.dirname(file.name)

    #loop through all the data for this chunk (previous chunk) and see what it is
    while (previous_chunk.bytes_read < previous_chunk.length):
        read_chunk(file, new_chunk)

        #is it a Version chunk?
        if new_chunk.ID == VERSION:
            #read in the version of the file
            temp_data = file.read(struct.calcsize('I'))
            version = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += 4  # read the 4 bytes for the version number
            #this loader works with version 3 and below, but may not with 4 and above
            if version > 3:
                print('\tNon-Fatal Error:  Version greater than 3, may not load correctly: ', version)

        #is it an object info chunk?
        elif new_chunk.ID == OBJECTINFO:
            process_next_chunk(context, file, new_chunk, importedObjects, IMAGE_SEARCH)

            #keep track of how much we read in the main chunk
            new_chunk.bytes_read += temp_chunk.bytes_read

        #is it an object chunk?
        elif new_chunk.ID == OBJECT:

            if CreateBlenderObject:
                putContextMesh(context, contextMesh_vertls, contextMesh_facels, contextMeshMaterials)
                contextMesh_vertls = []
                contextMesh_facels = []
                contextMeshMaterials = []
                contextMeshUV = None
                # Reset matrix
                contextMatrix = None

            CreateBlenderObject = True
            contextObName, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len

        #is it a material chunk?
        elif new_chunk.ID == MATERIAL:
            contextMaterial = bpy.data.materials.new('Material')
            contextWrapper = PrincipledBSDFWrapper(contextMaterial, is_readonly=False, use_nodes=False)

        elif new_chunk.ID == MAT_NAME:
            material_name, read_str_len = read_string(file)

            #plus one for the null character that ended the string
            new_chunk.bytes_read += read_str_len
            contextMaterial.name = material_name.rstrip()  # remove trailing  whitespace
            MATDICT[material_name] = contextMaterial

        elif new_chunk.ID == MAT_AMBIENT:
            read_chunk(file, temp_chunk)
            # only available color is emission color
               if temp_chunk.ID == MAT_FLOAT_COLOR:
               contextMaterial.line_color[:3] = read_float_color(temp_chunk)
            elif temp_chunk.ID == MAT_24BIT_COLOR:
                contextMaterial.line_color[:3] = read_byte_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_DIFFUSE:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == MAT_FLOAT_COLOR:
                contextMaterial.diffuse_color[:3] = read_float_color(temp_chunk)
            elif temp_chunk.ID == MAT_24BIT_COLOR:
                contextMaterial.diffuse_color[:3] = read_byte_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SPECULAR:
            read_chunk(file, temp_chunk)
            # Specular color is available
            if temp_chunk.ID == MAT_FLOAT_COLOR:
                contextMaterial.specular_color = read_float_color(temp_chunk)
            elif temp_chunk.ID == MAT_24BIT_COLOR:
                contextMaterial.specular_color = read_byte_color(temp_chunk)
            else:
                skip_to_end(file, temp_chunk)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_TEXTURE_MAP:
            read_texture(new_chunk, temp_chunk, "Diffuse", "COLOR")

        elif new_chunk.ID == MAT_SPECULAR_MAP:
            read_texture(new_chunk, temp_chunk, "Specular", "SPECULARITY")

        elif new_chunk.ID == MAT_OPACITY_MAP:
            read_texture(new_chunk, temp_chunk, "Opacity", "ALPHA")

        elif new_chunk.ID == MAT_REFLECTION_MAP:
            read_texture(new_chunk, temp_chunk, "Reflect", "METALLIC")

        elif new_chunk.ID == MAT_BUMP_MAP:
            read_texture(new_chunk, temp_chunk, "Bump", "NORMAL")

        elif new_chunk.ID == MAT_BUMP_PERCENT:
            temp_data = file.read(SZ_U_SHORT)
            new_chunk.bytes_read += SZ_U_SHORT
            contextWrapper.normalmap_strength = (float(struct.unpack('<H', temp_data)[0]) / 100)
            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN_MAP:
            read_texture(new_chunk, temp_chunk, "Shininess", "ROUGHNESS")

        elif new_chunk.ID == MAT_SELFI_MAP:
            read_texture(new_chunk, temp_chunk, "Emit", "EMISSION")

        elif new_chunk.ID == MAT_TEX2_MAP:
            read_texture(new_chunk, temp_chunk, "Tex", "TEXTURE")

        elif new_chunk.ID == MAT_SHINESS:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PERCENTAGE_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.roughness = 1 - (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PERCENTAGE_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.roughness = 1 - float(struct.unpack('f', temp_data)[0])

            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN2:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PERCENTAGE_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.specular_intensity = (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PERCENTAGE_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.specular_intensity = float(struct.unpack('f', temp_data)[0])

            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_SHIN3:
            read_chunk(file, temp_chunk)
            if temp_chunk.ID == PERCENTAGE_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.metallic = (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PERCENTAGE_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.metallic = float(struct.unpack('f', temp_data)[0])

            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == MAT_TRANSPARENCY:
            read_chunk(file, temp_chunk)

            if temp_chunk.ID == PERCENTAGE_SHORT:
                temp_data = file.read(SZ_U_SHORT)
                temp_chunk.bytes_read += SZ_U_SHORT
                contextMaterial.diffuse_color[3] = 1 - (float(struct.unpack('<H', temp_data)[0]) / 100)
            elif temp_chunk.ID == PERCENTAGE_FLOAT:
                temp_data = file.read(SZ_FLOAT)
                temp_chunk.bytes_read += SZ_FLOAT
                contextMaterial.diffuse_color[3] = 1 - float(struct.unpack('f', temp_data)[0])
            else:
                print( "Cannot read material transparency")

            new_chunk.bytes_read += temp_chunk.bytes_read

        elif new_chunk.ID == OBJECT_LIGHT:  # Basic lamp support.
            # no lamp in dict that would be confusing
            # ...why not? just set CreateBlenderObject to False
            newLamp = bpy.data.lights.new(contextObName, 'POINT')
            contextLamp = bpy.data.objects.new("Light", newLamp)
            context.view_layer.active_layer_collection.collection.objects.link(newLamp)
            importedObjects.append(contextLamp)
            temp_data = file.read(SZ_3FLOAT)
            contextLamp.location = struct.unpack('<3f', temp_data)
            new_chunk.bytes_read += SZ_3FLOAT
            CreateBlenderObject = False
            # Reset matrix
            contextMatrix = None

        elif new_chunk.ID == RGB:
            temp_data = file.read(SZ_3FLOAT)
            contextLamp.data.color = struct.unpack('<3f', temp_data)
            new_chunk.bytes_read += SZ_3FLOAT

        elif new_chunk.ID == OBJECT_MESH:
            pass
        
        elif new_chunk.ID == OBJECT_VERTICES:
            """Worldspace vertex locations"""
            
            temp_data = file.read(SZ_U_SHORT)
            num_verts = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2
            contextMesh_vertls = struct.unpack('<%df' % (num_verts * 3), file.read(SZ_3FLOAT * num_verts))
            new_chunk.bytes_read += SZ_3FLOAT * num_verts
            # dummyvert is not used atm!

        elif new_chunk.ID == OBJECT_FACES:
            temp_data = file.read(SZ_U_SHORT)
            num_faces = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2
            temp_data = file.read(SZ_4U_SHORT * num_faces)
            new_chunk.bytes_read += SZ_4U_SHORT * num_faces  # 4 short ints x 2 bytes each
            contextMesh_facels = struct.unpack('<%dH' % (num_faces * 4), temp_data)
            contextMesh_facels = [contextMesh_facels[i - 3:i] for i in range(3, (num_faces * 4) + 3, 4)]

        elif new_chunk.ID == OBJECT_MATERIAL:
            material_name, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len  # remove 1 null character.
            temp_data = file.read(SZ_U_SHORT)
            num_faces_using_mat = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += SZ_U_SHORT
            temp_data = file.read(SZ_U_SHORT * num_faces_using_mat)
            new_chunk.bytes_read += SZ_U_SHORT * num_faces_using_mat
            temp_data = struct.unpack("<%dH" % (num_faces_using_mat), temp_data)
            contextMeshMaterials.append((material_name, temp_data))
            #look up the material in all the materials

        elif new_chunk.ID == OBJECT_UV:
            temp_data = file.read(SZ_U_SHORT)
            num_uv = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2
            temp_data = file.read(SZ_2FLOAT * num_uv)
            new_chunk.bytes_read += SZ_2FLOAT * num_uv
            contextMeshUV = struct.unpack('<%df' % (num_uv * 2), temp_data)

        elif new_chunk.ID == OBJECT_TRANS_MATRIX:
            # How do we know the matrix size? 54 == 4x4 48 == 4x3
            temp_data = file.read(SZ_4x3MAT)
            data = list(struct.unpack('<ffffffffffff', temp_data))
            new_chunk.bytes_read += SZ_4x3MAT
            contextMatrix = mathutils.Matrix((data[:3]+[0], data[3:6]+[0], data[6:9]+[0], data[9:]+[1])).transposed()

        elif  (new_chunk.ID == MAT_MAP_FILEPATH):
            texture_name, read_str_len = read_string(file)
            if contextMaterial.name not in TEXTURE_DICT:
                TEXTURE_DICT[contextMaterial.name] = load_image(texture_name, dirname, place_holder=False, recursive=IMAGE_SEARCH)

            new_chunk.bytes_read += read_str_len  # plus one for the null character that gets removed
        elif new_chunk.ID == EDITKEYFRAME:
            pass
        
        elif new_chunk.ID == KFDATA_KFSEG:
            temp_data = file.read(struct.calcsize('I'))
            start = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += 4
            context.scene.frame_start = start
            temp_data = file.read(struct.calcsize('I'))
            stop = struct.unpack('<I', temp_data)[0]
            new_chunk.bytes_read += 4
            context.scene.frame_end = stop

        # including these here means their EK_OB_NODE_HEADER are scanned
        elif new_chunk.ID in {KFDATA_AMBIENT, ED_KEY_OBJECT_NODE, KFDATA_CAMERA, KFDATA_TARGET, KFDATA_LIGHT}:  # another object is being processed
            child = None

        elif new_chunk.ID in {EK_OB_NODE_HEADER, KFDATA_LIGHT}:
            object_name, read_str_len = read_string(file)
            new_chunk.bytes_read += read_str_len
            temp_data = file.read(SZ_U_SHORT * 2)
            new_chunk.bytes_read += 4
            temp_data = file.read(SZ_U_SHORT)
            hierarchy = struct.unpack('<H', temp_data)[0]
            new_chunk.bytes_read += 2
            child = object_dictionary.get(object_name)

            if child is None:
                child = bpy.data.objects.new(object_name, None)  # create an empty object
                context.view_layer.active_layer_collection.collection.objects.link(child)
                importedObjects.append(child)

            object_list.append(child)
            object_parent.append(hierarchy)
            pivot_list.append(mathutils.Vector((0.0, 0.0, 0.0)))

        elif new_chunk.ID == EK_OB_INSTANCE_NAME:
            object_name, read_str_len = read_string(file)
            if child.name == '$$$DUMMY':
                child.name = object_name
            else: child.name += "." + object_name
            object_dictionary[object_name] = child
            new_chunk.bytes_read += read_str_len

        elif new_chunk.ID == EK_OB_PIVOT:  # translation
                temp_data = file.read(SZ_3FLOAT)
                pivot = struct.unpack('<3f', temp_data)
                new_chunk.bytes_read += SZ_3FLOAT
                pivot_list[len(pivot_list) - 1] = mathutils.Vector(pivot)

        elif new_chunk.ID == EK_OB_POSITION_TRACK:  # translation
            new_chunk.bytes_read += SZ_U_SHORT * 5
            temp_data = file.read(SZ_U_SHORT * 5)
            temp_data = file.read(SZ_U_SHORT)
            nkeys = struct.unpack('<H', temp_data)[0]
            temp_data = file.read(SZ_U_SHORT)
            new_chunk.bytes_read += SZ_U_SHORT * 2
            for i in range(nkeys):
                temp_data = file.read(SZ_U_SHORT)
                nframe = struct.unpack('<H', temp_data)[0]
                new_chunk.bytes_read += SZ_U_SHORT
                temp_data = file.read(SZ_U_SHORT * 2)
                new_chunk.bytes_read += SZ_U_SHORT * 2
                temp_data = file.read(SZ_3FLOAT)
                loc = struct.unpack('<3f', temp_data)
                new_chunk.bytes_read += SZ_3FLOAT
                if nframe == 0:
                    child.location = loc

        elif new_chunk.ID == EK_OB_ROTATION_TRACK and child.type == 'MESH':  # rotation
            new_chunk.bytes_read += SZ_U_SHORT * 5
            temp_data = file.read(SZ_U_SHORT * 5)
            temp_data = file.read(SZ_U_SHORT)
            nkeys = struct.unpack('<H', temp_data)[0]
            temp_data = file.read(SZ_U_SHORT)
            new_chunk.bytes_read += SZ_U_SHORT * 2
            for i in range(nkeys):
                temp_data = file.read(SZ_U_SHORT)
                nframe = struct.unpack('<H', temp_data)[0]
                new_chunk.bytes_read += SZ_U_SHORT
                temp_data = file.read(SZ_U_SHORT * 2)
                new_chunk.bytes_read += SZ_U_SHORT * 2
                temp_data = file.read(SZ_4FLOAT)
                rad, axis_x, axis_y, axis_z = struct.unpack("<4f", temp_data)
                new_chunk.bytes_read += SZ_4FLOAT
                if nframe == 0:
                    child.rotation_euler = mathutils.Quaternion((axis_x, axis_y, axis_z), -rad).to_euler()   # why negative?

        elif new_chunk.ID == EK_OB_SCALE_TRACK and child.type == 'MESH':  # translation
            new_chunk.bytes_read += SZ_U_SHORT * 5
            temp_data = file.read(SZ_U_SHORT * 5)
            temp_data = file.read(SZ_U_SHORT)
            nkeys = struct.unpack('<H', temp_data)[0]
            temp_data = file.read(SZ_U_SHORT)
            new_chunk.bytes_read += SZ_U_SHORT * 2
            for i in range(nkeys):
                temp_data = file.read(SZ_U_SHORT)
                nframe = struct.unpack('<H', temp_data)[0]
                new_chunk.bytes_read += SZ_U_SHORT
                temp_data = file.read(SZ_U_SHORT * 2)
                new_chunk.bytes_read += SZ_U_SHORT * 2
                temp_data = file.read(SZ_3FLOAT)
                sca = struct.unpack('<3f', temp_data)
                new_chunk.bytes_read += SZ_3FLOAT
                if nframe == 0:
                    child.scale = sca

        elif new_chunk.ID == EK_OB_COLOR_TRACK and child.type == 'LIGHT':  # Color
            new_chunk.bytes_read += SZ_U_SHORT * 5
            temp_data = file.read(SZ_U_SHORT * 5)
            temp_data = file.read(SZ_U_SHORT)
            nkeys = struct.unpack('<H', temp_data)[0]
            temp_data = file.read(SZ_U_SHORT)
            new_chunk.bytes_read += SZ_U_SHORT * 2
            for i in range(nkeys):
                temp_data = file.read(SZ_U_SHORT)
                nframe = struct.unpack('<H', temp_data)[0]
                new_chunk.bytes_read += SZ_U_SHORT
                temp_data = file.read(SZ_U_SHORT * 2)
                new_chunk.bytes_read += SZ_U_SHORT * 2
                temp_data = file.read(SZ_3FLOAT)
                rgb = struct.unpack('<3f', temp_data)
                new_chunk.bytes_read += SZ_3FLOAT
                if nframe == 0:
                    child.scale = rgb

        else:
            buffer_size = new_chunk.length - new_chunk.bytes_read
            binary_format = "%ic" % buffer_size
            temp_data = file.read(struct.calcsize(binary_format))
            new_chunk.bytes_read += buffer_size

        #update the previous chunk bytes read
        previous_chunk.bytes_read += new_chunk.bytes_read

    # FINISHED LOOP
    # There will be a number of objects still not added
    if CreateBlenderObject:
        putContextMesh(context, contextMesh_vertls, contextMesh_facels, contextMeshMaterials)

    # Assign parents to objects
    # check _if_ we need to assign first because doing so recalcs the depsgraph
    for ind, ob in enumerate(object_list):
        parent = object_parent[ind]
        if parent == ROOT_OBJECT:
            if ob.parent is not None:
                ob.parent = None
        else:
            if ob.parent != object_list[parent]:
                if ob == object_list[parent]:
                    print('   warning: Cannot assign self to parent ', ob)
                else:
                    ob.parent = object_list[parent]

            # pivot_list[ind] += pivot_list[parent]  # XXX, not sure this is correct, should parent space matrix be applied before combining?
    # fix pivots
    for ind, ob in enumerate(object_list):
        if ob.type == 'MESH':
            pivot = pivot_list[ind]
            pivot_matrix = object_matrix.get(ob, mathutils.Matrix())  # unlikely to fail
            pivot_matrix = mathutils.Matrix.Translation(-1*pivot)
            #pivot_matrix = mathutils.Matrix.Translation(pivot_matrix.to_3x3() @ -pivot)
            ob.data.transform(pivot_matrix)


def load_3ds(filepath,
             context,
             IMPORT_CONSTRAIN_BOUNDS=10.0,
             IMAGE_SEARCH=True,
             APPLY_MATRIX=True,
             global_matrix=None):
#    global SCN

    # XXX
#   if BPyMessages.Error_NoFile(filepath):
#       return

    print("importing 3DS: %r..." % (filepath), end="")

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.clock()
#   time1 = Blender.sys.time()

    current_chunk = Chunk()

    file = open(filepath, 'rb')

    #here we go!
    # print 'reading the first chunk'
    read_chunk(file, current_chunk)
    if current_chunk.ID != PRIMARY:
        print('\tFatal Error:  Not a valid 3ds file: %r' % filepath)
        file.close()
        return

    if IMPORT_CONSTRAIN_BOUNDS:
        BOUNDS_3DS[:] = [1 << 30, 1 << 30, 1 << 30, -1 << 30, -1 << 30, -1 << 30]
    else:
        del BOUNDS_3DS[:]

    ##IMAGE_SEARCH

    # fixme, make unglobal, clear in case
    object_dictionary.clear()
    object_matrix.clear()

    scn = context.scene

    importedObjects = []  # Fill this list with objects
    process_next_chunk(context, file, current_chunk, importedObjects, IMAGE_SEARCH)

    # fixme, make unglobal
    object_dictionary.clear()
    object_matrix.clear()

    # Link the objects into this scene.
    # Layers = scn.Layers

    # REMOVE DUMMYVERT, - remove this in the next release when blenders internal are fixed.

    if APPLY_MATRIX:
        for ob in importedObjects:
            if ob.type == 'MESH':
                me = ob.data
                me.transform(ob.matrix_local.inverted())

    # print(importedObjects)
    if global_matrix:
        for ob in importedObjects:
            if ob.type == 'MESH' and ob.parent is None:
                ob.matrix_world = ob.matrix_world @ global_matrix

    for ob in importedObjects:
        ob.select_set(True)

    # Done DUMMYVERT
    """
    if IMPORT_AS_INSTANCE:
        name = filepath.split('\\')[-1].split('/')[-1]
        # Create a group for this import.
        group_scn = Scene.New(name)
        for ob in importedObjects:
            group_scn.link(ob) # dont worry about the layers

        grp = Blender.Group.New(name)
        grp.objects = importedObjects

        grp_ob = Object.New('Empty', name)
        grp_ob.enableDupGroup = True
        grp_ob.DupGroup = grp
        scn.link(grp_ob)
        grp_ob.Layers = Layers
        grp_ob.sel = 1
    else:
        # Select all imported objects.
        for ob in importedObjects:
            scn.link(ob)
            ob.Layers = Layers
            ob.sel = 1
    """

    context.view_layer.update()

    axis_min = [1000000000] * 3
    axis_max = [-1000000000] * 3
    global_clight_size = IMPORT_CONSTRAIN_BOUNDS
    if global_clight_size != 0.0:
        # Get all object bounds
        for ob in importedObjects:
            for v in ob.bound_box:
                for axis, value in enumerate(v):
                    if axis_min[axis] > value:
                        axis_min[axis] = value
                    if axis_max[axis] < value:
                        axis_max[axis] = value

        # Scale objects
        max_axis = max(axis_max[0] - axis_min[0],
                       axis_max[1] - axis_min[1],
                       axis_max[2] - axis_min[2])
        scale = 1.0

        while global_clight_size < max_axis * scale:
            scale = scale / 10.0

        scale_mat = mathutils.Matrix.Scale(scale, 4)

        for obj in importedObjects:
            if obj.parent is None:
                obj.matrix_world = scale_mat @ obj.matrix_world

    # Select all new objects.
    print(" done in %.4f sec." % (time.clock() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         constrain_size=0.0,
         use_image_search=True,
         use_apply_transform=True,
         global_matrix=None,
         ):

    load_3ds(filepath,
             context,
             IMPORT_CONSTRAIN_BOUNDS=constrain_size,
             IMAGE_SEARCH=use_image_search,
             APPLY_MATRIX=use_apply_transform,
             global_matrix=global_matrix,
             )

    return {'FINISHED'}
