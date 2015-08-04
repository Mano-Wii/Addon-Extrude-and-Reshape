### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# Contact for more information about the Addon:
# Email:    germano.costa@ig.com.br
# Twitter:  wii_mano @mano_wii

bl_info = {
    "name": "Push Pull Face",
    "author": "Germano Cavalcante",
    "version": (0, 5),
    "blender": (2, 75, 0),
    "location": "View3D > TOOLS > Tools > Mesh Tools > Add: > Extrude Menu (Alt + E)",
    "description": "Push and pull face entities to sculpt 3d models",
    "wiki_url" : "http://blenderartists.org/forum/showthread.php?376618-Addon-Push-Pull-Face",
    "category": "Mesh"}

import bpy
import bmesh
from mathutils import Vector
from bpy.props import FloatProperty

def intersect_bound_box_edge_edge(a1, a2, b1, b2, precision = 0.0001):
    bbx1 = sorted([a1.x, a2.x])
    bbx2 = sorted([b1.x, b2.x])
    if ((bbx1[0] - precision) <= bbx2[1]) and (bbx1[1] >= (bbx2[0] - precision)):
        bby1 = sorted([a1.y, a2.y])
        bby2 = sorted([b1.y, b2.y])
        if ((bby1[0] - precision) <= bby2[1]) and (bby1[1] >= (bby2[0] - precision)):
            bbz1 = sorted([a1.z, a2.z])
            bbz2 = sorted([b1.z, b2.z])
            if ((bbz1[0] - precision) <= bbz2[1]) and (bbz1[1] >= (bbz2[0] - precision)):
                return True
            else:
                return False
        else:
            return False
    else:
        return False

def intersect_edges_edges(edges1, edges2, ignore = {}, precision = 4):
    fprec = .1**precision
    new_edges1 = set()
    new_edges2 = set()
    targetmap = {}
    exclude = {}
    for ed1 in edges1:
        for ed2 in edges2:
            if ed1 != ed2 and (ed1 not in ignore or ed2 not in ignore[ed1]):
                a1 = ed1.verts[0]
                a2 = ed1.verts[1]
                b1 = ed2.verts[0]
                b2 = ed2.verts[1]
                intersect = intersect_bound_box_edge_edge(a1.co, a2.co, b1.co, b2.co, precision = fprec)
                if intersect:
                    v1 = a2.co-a1.co
                    v2 = b2.co-b1.co
                    v3 = a1.co-b1.co
                    
                    cross1 = v3.cross(v1)
                    cross2 = v3.cross(v2)
                    
                    crosscross = cross1.cross(cross2)
                    if crosscross.to_tuple(2) == (0,0,0): #cross cross is very inaccurate
                        cross3 = v2.cross(v1)
                        lc3 = cross3.x+cross3.y+cross3.z

                        if abs(lc3) > fprec: 
                            lc1 = cross1.x+cross1.y+cross1.z
                            lc2 = cross2.x+cross2.y+cross2.z
                            
                            fac1 = lc2/lc3
                            fac2 = lc1/lc3
                            if 0 <= fac1 <= 1 and 0 <= fac2 <= 1:
                                rfac1 = round(fac1, precision)
                                rfac2 = round(fac2, precision)
                                set_ign = {ed2}

                                if 0 < rfac2 < 1:
                                    ne2, nv2 = bmesh.utils.edge_split(ed2, b1, fac2)
                                    new_edges2.update({ed2, ne2})
                                    set_ign.add(ne2)
                                elif rfac2 == 0:
                                    nv2 = b1
                                else:
                                    nv2 = b2

                                if 0 < rfac1 < 1:
                                    ne1, nv1 = bmesh.utils.edge_split(ed1, a1, fac1)
                                    new_edges1.update({ed1, ne1})
                                    exclude[ed1] = exclude[ne1] = set_ign
                                elif rfac1 == 0:
                                    nv1 = a1
                                    exclude[ed1] = set_ign
                                else:
                                    nv1 = a2
                                    exclude[ed1] = set_ign

                                if nv1 != nv2:
                                    targetmap[nv1] = nv2
                            #else:                            
                                #print('not intersect')
                        #else:
                            #print('colinear')
                    #else:
                        #print('not coplanar')
    if new_edges1 or new_edges2:
        edges1.update(new_edges1)
        ned, tar = intersect_edges_edges(edges1, new_edges2, ignore = exclude, precision = precision)
        if tar != targetmap:
            new_edges1.update(ned["new_edges1"])
            new_edges2.update(ned["new_edges2"])
            targetmap.update(tar)
        return {"new_edges1": new_edges1,
                "new_edges2": new_edges2
                }, targetmap
    else:
        return {"new_edges1": new_edges1,
                "new_edges2": new_edges2
                }, targetmap

class Push_Pull_Face(bpy.types.Operator):
    """Push and pull face entities to sculpt 3d models"""
    bl_idname = "mesh.push_pull_face"
    bl_label = "Push/Pull Face"
    bl_options = {'REGISTER', 'GRAB_CURSOR', 'BLOCKING'}

    @classmethod
    def poll(cls, context):
        return context.mode is not 'EDIT_MESH'

    def modal(self, context, event):
        op = context.window_manager.operators
        #print([o.name for o in op])
        if op and op[-1].name == 'Translate':
            #print('-------------------')
            sface = self.bm.faces.active
            set_edges = set()
            for v in sface.verts:
                for ed in v.link_edges:
                    set_edges.add(ed)
            bm_edges = set(self.bm.edges)#.difference_update(set_edges)
            bm_edges.difference_update(set_edges)
            new_edges, targetmap = intersect_edges_edges(set_edges, bm_edges)
            if targetmap:
                bmesh.ops.weld_verts(self.bm, targetmap=targetmap)
            bmesh.update_edit_mesh(self.mesh, tessface=True, destructive=True)
            return {'FINISHED'}
        if self.cancel:
            return {'FINISHED'}
        self.cancel = event.type == 'ESC'
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.mesh = context.object.data
        self.bm = bmesh.from_edit_mesh(self.mesh)
        try:
            selection = self.bm.select_history[0]
        except:
            for face in self.bm.faces:
                if face.select == True:
                    selection = face
                    break
            else:
                return {'FINISHED'}
        if not isinstance(selection, bmesh.types.BMFace):
            bpy.ops.mesh.extrude_region_move('INVOKE_DEFAULT')
            return {'FINISHED'}
        else:
            face = selection
            geom = []
            for edge in face.edges:
                if abs(edge.calc_face_angle(0) - 1.5707963267948966) < 0.01: #self.angle_tolerance:
                    geom.append(edge)

            dict = bmesh.ops.extrude_discrete_faces(self.bm, faces = [face])
            bpy.ops.mesh.select_all(action='DESELECT')
            for face in dict['faces']:
                self.bm.faces.active = face
                face.select = True
                sface = face
            dfaces = bmesh.ops.dissolve_edges(self.bm, edges = geom, use_verts=True, use_face_split=False)
            bmesh.update_edit_mesh(self.mesh, tessface=True, destructive=True)
            bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(False, False, True), constraint_orientation='NORMAL', release_confirm=True)
            self.face_id = sface.index
        #return {'FINISHED'}
        rv3d = context.region_data
        rv3d.view_location = rv3d.view_location
        context.window_manager.modal_handler_add(self)

        self.cancel = False
        return {'RUNNING_MODAL'}

def operator_draw(self,context):
    layout = self.layout
    col = layout.column(align=True)
    col.operator("mesh.push_pull_face", text="Push/Pull Face")

def register():
    bpy.utils.register_class(Push_Pull_Face)
    bpy.types.VIEW3D_MT_edit_mesh_extrude.append(operator_draw)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_extrude.remove(operator_draw)
    bpy.utils.unregister_class(Push_Pull_Face)

if __name__ == "__main__":
    register()
