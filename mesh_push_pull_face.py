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
    "version": (0, 6),
    "blender": (2, 75, 0),
    "location": "View3D > TOOLS > Tools > Mesh Tools > Add: > Extrude Menu (Alt + E)",
    "description": "Push and pull face entities to sculpt 3d models",
    "wiki_url" : "http://blenderartists.org/forum/showthread.php?376618-Addon-Push-Pull-Face",
    "category": "Mesh"}

import bpy
import bmesh
#from mathutils import Vector
from bpy.props import FloatProperty

def edges_BVH_overlap(edges1, edges2, precision = 0.0001):
    l1 = [e.verts for e in edges1]
    l2 = [e.verts for e in edges2]
    aco = [(v1.co,v2.co) for v1,v2 in l1]
    bco = [(v1.co,v2.co) for v1,v2 in l2]
    tmp_set1 = set()
    tmp_set2 = set()
    overlay = {}
    oget = overlay.get
    for i1, ed1 in enumerate(aco):
        for i2, ed2 in enumerate(bco):
            if ed1 != ed2:
                a1, a2 = ed1
                b1, b2 = ed2

                a1x, a2x = a1.x, a2.x
                b1x, b2x = b1.x, b2.x
                bbx1 = (a1x, a2x) if a1x < a2x else (a2x, a1x)
                bbx2 = (b1x, b2x) if b1x < b2x else (b2x, b1x)
                if (bbx1[0] - precision) <= bbx2[1] and bbx1[1] >= (bbx2[0] - precision):
                    a1y, a2y = a1.y, a2.y
                    b1y, b2y = b1.y, b2.y
                    bby1 = (a1y, a2y) if a1y < a2y else (a2y, a1y)
                    bby2 = (b1y, b2y) if b1y < b2y else (b2y, b1y)
                    if (bby1[0] - precision) <= bby2[1] and bby1[1] >= (bby2[0] - precision):
                        a1z, a2z = a1.z, a2.z
                        b1z, b2z = b1.z, b2.z
                        bbz1 = (a1z, a2z) if a1z < a2z else (a2z, a1z)
                        bbz2 = (b1z, b2z) if b1z < b2z else (b2z, b1z)
                        if (bbz1[0] - precision) <= bbz2[1] and bbz1[1] >= (bbz2[0] - precision):
                            e1 = edges1[i1]
                            tmp_set1.add(e1)
                            tmp_set2.add(edges2[i2])
                            #overlay[e1.index] = oget(e1.index, set()).union({edges2[i2].index})
                            overlay[e1] = oget(e1, set()).union({edges2[i2]})

    return tmp_set1, tmp_set2, overlay

def intersect_edges_edges(overlay, ignore = {}, precision = 4):
    sp = 0
    fprec = .1**precision
    splits = {}
    sp_get = splits.get
    new_edges1 = set()
    new_edges2 = set()
    targetmap = {}
    exclude = {}
    get = ignore.get
    for edg1 in overlay:
        #print(sp, edg1.index)
        sp = 0
        splits[edg1] = set()
        while len(overlay[edg1]) > sp: #.difference(splits[edg1]):
            ed1 = edg1
            fi = True
            for ed2 in overlay[edg1].difference(splits[edg1]):
                # test if repeats
                #if ed2 not in get(ed1, set()):
                a1 = ed1.verts[0] # to do check ed1
                a2 = ed1.verts[1] # to do check ed1
                b1 = ed2.verts[0]
                b2 = ed2.verts[1]
                
                # test if are linked
                if a1 in {b1, b2} or a2 in {b1, b2}:
                    sp += 1
                    continue
                #print('oi')

                v1 = a2.co-a1.co
                v2 = b2.co-b1.co
                v3 = a1.co-b1.co
                
                cross1 = v3.cross(v1)
                cross2 = v3.cross(v2)
                lc1 = cross1.x+cross1.y+cross1.z
                lc2 = cross2.x+cross2.y+cross2.z
                
                try:
                    coplanar = (cross1/lc1).cross(cross2/lc2).to_tuple(2) == (0,0,0) #cross cross is very inaccurate
                except ZeroDivisionError:
                    coplanar = (cross1).cross(cross2).to_tuple(2) == (0,0,0)
                
                if coplanar:
                    cross3 = v2.cross(v1)
                    lc3 = cross3.x+cross3.y+cross3.z

                    # test if are colinear (coliner is ignored)
                    if abs(lc3) > fprec:
                        fac1 = lc2/lc3
                        fac2 = lc1/lc3
                        
                        # finally tests if intersect
                        if 0 <= fac1 <= 1 and 0 <= fac2 <= 1: # Use while?
                            pass
                        elif ed2 in splits:
                            for ed2 in splits[ed2]:
                                b1 = ed2.verts[0]
                                b2 = ed2.verts[1]

                                v2 = b2.co-b1.co
                                v3 = a1.co-b1.co

                                cross1 = v3.cross(v1)
                                cross2 = v3.cross(v2)
                                cross3 = v2.cross(v1)

                                lc1 = cross1.x+cross1.y+cross1.z
                                lc2 = cross2.x+cross2.y+cross2.z
                                lc3 = cross3.x+cross3.y+cross3.z

                                fac1 = lc2/lc3
                                fac2 = lc1/lc3

                                if 0 <= fac1 <= 1 and 0 <= fac2 <= 1: # Use while?
                                    break
                            else:
                                #print('not intersect2')
                                if fi:
                                    sp += 1
                                continue
                        else:
                            #print('not intersect')
                            if fi:
                                sp += 1
                            continue
                            
                        rfac1 = round(fac1, precision)
                        rfac2 = round(fac2, precision)
                        sp += 1

                        if 0 < rfac1 < 1:
                            ne1, nv1 = bmesh.utils.edge_split(ed1, a1, fac1)
                            new_edges1.update({ed1, ne1})
                            splits[ed1] = sp_get(ed1, set()).union({ne1})
                            ed1 = ne1
                            fi = False
                        elif rfac1 == 0:
                            nv1 = a1
                        else:
                            nv1 = a2

                        if 0 < rfac2 < 1:
                            ne2, nv2 = bmesh.utils.edge_split(ed2, b1, fac2)
                            new_edges2.update({ed2, ne2})
                            splits[ed2] = sp_get(ed2, set()).union({ne2})
                        elif rfac2 == 0:
                            nv2 = b1
                        else:
                            nv2 = b2

                        if nv1 != nv2: # test unnecessary!!!
                            targetmap[nv1] = nv2
                    elif fi:
                        sp += 1
                        #print('colinear')
                elif fi:
                    sp += 1
                    #print('not coplanar')

    return new_edges1, new_edges2, targetmap

class Push_Pull_Face(bpy.types.Operator):
    """Push and pull face entities to sculpt 3d models"""
    bl_idname = "mesh.push_pull_face"
    bl_label = "Push/Pull Face"
    bl_options = {'REGISTER', 'GRAB_CURSOR', 'BLOCKING'}

    @classmethod
    def poll(cls, context):
        return  context.mode is not 'EDIT_MESH'

    def modal(self, context, event):
        if self.confirm:
            sface = self.bm.faces.active
            if not sface:
                for face in self.bm.faces:
                    if face.select == True:
                        sface = face
                        break
                else:
                    return {'FINISHED'}
            edges = set()
            for v in sface.verts:
                for ed in v.link_edges:
                    edges.add(ed)
            edges = list(edges)
            bm_edges = self.bm.edges
            set_edges, bm_edges, overlay = edges_BVH_overlap(edges, bm_edges, precision = 0.0001)
            overlay = {k: v.difference(overlay) for k,v in overlay.items()} # remove repetition
            new_edges1, new_edges2, targetmap = intersect_edges_edges(overlay)
            if targetmap:
                bmesh.ops.weld_verts(self.bm, targetmap=targetmap)
            print([e.is_valid for e in new_edges1])
            print([e.is_valid for e in new_edges2])
            for e in new_edges2:
                lfe = set(e.link_faces)
                v1, v2 = e.verts
                lf1 = set(v1.link_faces)
                lf2 = set(v2.link_faces)
                rlfe = lf1.intersection(lf2)
                for f in rlfe.difference(lfe):
                    bmesh.utils.face_split(f, v1, v2)
            
            bmesh.update_edit_mesh(self.mesh, tessface=True, destructive=True)
            return {'FINISHED'}
        if self.cancel:
            return {'FINISHED'}
        self.cancel = event.type == 'ESC'
        self.confirm = event.type == 'LEFTMOUSE'
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.mesh = context.object.data
        self.bm = bmesh.from_edit_mesh(self.mesh)
        try:
            selection = self.bm.select_history[-1]
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
            #face.select = False
            bpy.ops.mesh.select_all(action='DESELECT')
            geom = []
            for edge in face.edges:
                if abs(edge.calc_face_angle(0) - 1.5707963267948966) < 0.01: #self.angle_tolerance:
                    geom.append(edge)

            dict = bmesh.ops.extrude_discrete_faces(self.bm, faces = [face])
            
            for face in dict['faces']:
                self.bm.faces.active = face
                face.select = True
                sface = face
            dfaces = bmesh.ops.dissolve_edges(self.bm, edges = geom, use_verts=True, use_face_split=False)
            bmesh.update_edit_mesh(self.mesh, tessface=True, destructive=True)
            bpy.ops.transform.translate('INVOKE_DEFAULT', constraint_axis=(False, False, True), constraint_orientation='NORMAL', release_confirm=True)

        context.window_manager.modal_handler_add(self)

        self.cancel = False
        self.confirm = False
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
