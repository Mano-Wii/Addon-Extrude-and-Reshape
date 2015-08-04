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
    "version": (0, 4),
    "blender": (2, 75, 0),
    "location": "View3D > TOOLS > Tools > Mesh Tools > Add: > Extrude Menu (Alt + E)",
    "description": "Push and pull face entities to sculpt 3d models",
    #"wiki_url" : "http://blenderartists.org/forum/",
    "category": "Mesh"}

import bpy
import bmesh
from mathutils import Vector
from bpy.props import FloatProperty

def get_coplanar_faces(bm, face, precision = 4):
    faces = []
    nn = -face.normal
    normals = face.normal.to_tuple(precision), nn.to_tuple(precision)
    m_face = face.calc_center_median()
    for f in bm.faces:
        #if f != face:
        n = f.normal.to_tuple(precision)
        if n in normals:
            vec = f.calc_center_median() - m_face
            if abs(vec.dot(n)) < 0.001 and f!= face:
                faces.append(f)
    return faces

def intersect_bound_box_face_edge(face, edge, precision = 4):
    l_f = 2*len(face.verts)
    x1 = 0
    x0 = 0
    y1 = 0
    y0 = 0
    z1 = 0
    z0 = 0
    for point in edge.verts:
        for v in face.verts:
            v = v.co - point.co
            dx, dy, dz = v.to_tuple(precision)
            if dx < 0:
                x0 += 1
            elif dx > 0:
                x1 += 1
            else:
                x0 -= 1
                x1 -= 1

            if dy < 0:
                y0 += 1
            elif dy > 0:
                y1 += 1
            else:
                y0 -= 1
                y1 -= 1

            if dz < 0:
                z0 += 1
            elif dz > 0:
                z1 += 1
            else:
                z0 -= 1
                z1 -= 1
    inside = True
    if x0 >= l_f or x1 >= l_f:
        inside = False
    if y0 >= l_f or y1 >= l_f:
        inside = False
    if z0 >= l_f or z1 >= l_f:
        inside = False
    return inside

def intersect_bound_box_edge_edge(edge1, edge2, precision = 4):
    x1 = 0
    x0 = 0
    y1 = 0
    y0 = 0
    z1 = 0
    z0 = 0    
    for v1 in edge1.verts:
        for v2 in edge2.verts:
            v = (v1.co - v2.co)
            dx, dy, dz = v.to_tuple(precision)
            if dx < 0:
                x0 += 1
            elif dx > 0:
                x1 += 1
            else:
                x0 -= 1
                x1 -= 1

            if dy < 0:
                y0 += 1
            elif dy > 0:
                y1 += 1
            else:
                y0 -= 1
                y1 -= 1

            if dz < 0:
                z0 += 1
            elif dz > 0:
                z1 += 1
            else:
                z0 -= 1
                z1 -= 1
    inside = True
    if x0 >= 4 or x1 >= 4:
        inside = False
    if y0 >= 4 or y1 >= 4:
        inside = False
    if z0 >= 4 or z1 >= 4:
        inside = False
    return inside

def intersect_face_edges(face, edges, ignore = {}, precision = 4):
    new_edges = []
    new_face_edges = []
    targetmap = {}
    exclude = {}
    for edge in edges:
        if edge in face.edges:
            intersect = True
        else:
            intersect = intersect_bound_box_face_edge(face, edge, precision = precision) #desnecessário para edge na face
        if intersect:
            for fedg in [e for e in face.edges if e not in edges]:
                if edge not in ignore or fedg not in ignore[edge]:
                    intersect2 = intersect_bound_box_edge_edge(edge, fedg, precision = precision)
                    if intersect2:
                        #print(edge.index, fedg.index)
                        ve0 = edge.verts[0]
                        vf0 = fedg.verts[0]

                        v1 = ve0.co
                        v2 = edge.verts[1].co
                        v3 = vf0.co
                        v4 = fedg.verts[1].co

                        c1 = (v3-v1).cross(v4-v1)
                        c2 = (v3-v2).cross(v4-v2)
                        c3 = (v1-v3).cross(v2-v3)
                        c4 = (v1-v4).cross(v2-v4)

                        c1l = (c1.x + c1.y + c1.z)
                        c2l = -(c2.x + c2.y + c2.z)
                        c3l = (c3.x + c3.y + c3.z)
                        c4l = -(c4.x + c4.y + c4.z)
                        
                        l = [c1l,c2l,c3l,c4l]
                        zeros = l.count(0)

                        if zeros == 0 and\
                           (c1l > 0) == (c2l > 0) and\
                           (c3l > 0) == (c4l > 0):

                            f1 = c1l/(c1l+c2l)
                            f2 = c3l/(c3l+c4l)

                            ef, vf = bmesh.utils.edge_split(fedg, vf0, f2)
                            new_face_edges += [fedg, ef]

                            e, v = bmesh.utils.edge_split(edge, ve0, f1)
                            new_edges += [edge, e]

                            exclude[edge] = exclude[e] = {fedg, ef}

                            targetmap[v] = vf

                        elif zeros == 1: #Será que não precisa testar cross por causa do intersect_bound_box_edge_edge???
                            if 0 not in {c1l,c2l} and (c1l > 0) != (c2l > 0):
                                continue
                            if 0 not in (c3l,c4l) and (c3l > 0) != (c4l > 0):
                                continue
                                
                            set_ign = {fedg}

                            f1 = c1l/(c1l+c2l)
                            f2 = c3l/(c3l+c4l)
                            
                            if f2 not in {0, 1}:
                                ef, vf = bmesh.utils.edge_split(fedg, vf0, f2)
                                new_face_edges += [fedg, ef]
                                set_ign.add(ef)
                            elif f2 == 0:
                                vf = vf0
                            else:
                                vf = fedg.verts[1]

                            if f1 not in {0, 1}:
                                e, v = bmesh.utils.edge_split(edge, ve0, f1)
                                new_edges += [edge, e]
                                exclude[edge] = exclude[e] = set_ign
                            elif f1 == 0:
                                v = ve0
                            else:
                                v = edge.verts[1]

                            targetmap[v] = vf
                            
                        else:
                            pass
                            #print('colienares')
                            
    if new_edges or new_face_edges:
        ned, tar = intersect_face_edges(face, new_edges, ignore = exclude, precision = precision)
        if tar != targetmap:
            targetmap.update(tar)
        return {"new_face_edges": new_face_edges + ned["new_face_edges"],
                "new_edges": new_edges + ned["new_face_edges"]
                }, targetmap
    else:
        return {"new_face_edges": new_face_edges,
                "new_edges": new_edges
                }, targetmap

class Push_Pull_Face(bpy.types.Operator):
    """Push and pull face entities to sculpt 3d models"""
    bl_idname = "mesh.push_pull_face"
    bl_label = "Push/Pull Face"
    bl_options = {'REGISTER', 'GRAB_CURSOR', 'BLOCKING'}

    angle_tolerance = FloatProperty(
            name="precision orthogonality",
            description="orthogonality tolerance of a face relative to another.",
            min=0.000000, max=3.141592653589793,
            default=0.01,
            )

    @classmethod
    def poll(cls, context):
        return context.mode is not 'EDIT_MESH'
    
    def face_hierarchy(self):
        self.bm.faces.ensure_lookup_table()
        try:
            sface = self.bm.faces[self.face_id]
        except: #IndexError or ReferenceError
            self.bm = bmesh.from_edit_mesh(self.mesh) # para ReferenceError
            for face in self.bm.faces:
                if face.select == True:
                    sface = face
                    break
            else:
                bmesh.update_edit_mesh(self.mesh, tessface=True, destructive=True)
                return {'FINISHED'}
        tface = {sface}
        targetmap = {}
        ignore = {}
        for loop in sface.loops:
            loop2 = loop.link_loops[0] #[0]!!!!!!!!!!!!!!!!!!!!!!!!
            face = loop2.face
            tface.add(face)            
            if len(face.verts) != 4:
                edges = [loop2.edge, loop2.link_loop_next.edge, loop2.link_loop_prev.edge]
                new_edges, tmpmap = intersect_face_edges(face, edges, precision = 4)
                targetmap.update(tmpmap)
                for e in new_edges['new_face_edges']:
                    ignore[e] = set()

        for face in tface:
            coplanar_faces = get_coplanar_faces(self.bm, face, precision = 4)
            set_edges = set()
            for f in coplanar_faces:
                for edge in f.edges:
                    set_edges.add(edge)
            new_edges2, tmpmap2 = intersect_face_edges(face, set_edges, ignore = ignore, precision = 4)
            targetmap.update(tmpmap2)

        if targetmap:
            bmesh.ops.weld_verts(self.bm, targetmap=targetmap)
        bmesh.update_edit_mesh(self.mesh, tessface=True, destructive=True)

    def modal(self, context, event):
        op = context.window_manager.operators
        #print([o.name for o in op])
        if op and op[-1].name == 'Translate':
            #print('-------------------')
            self.face_hierarchy()
            #bpy.ops.mesh.intersect(mode='SELECT_UNSELECT', use_separate=True, threshold=0.01)
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
                #print(edge.calc_face_angle()- 1.5707963267948966)
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