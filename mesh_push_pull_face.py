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
    "version": (0, 8),
    "blender": (2, 76, 0),
    "location": "View3D > TOOLS > Tools > Mesh Tools > Add: > Extrude Menu (Alt + E)",
    "description": "Push and pull face entities to sculpt 3d models",
    "wiki_url" : "http://blenderartists.org/forum/showthread.php?376618-Addon-Push-Pull-Face",
    "category": "Mesh"}

import bpy
import bmesh
from mathutils.geometry import intersect_line_line
from bpy.props import FloatProperty

def edges_BVH_overlap(edges1, edges2, epsilon = 0.0001):
    aco = ([v.co for v in e.verts] for e in edges1)
    bco = [[v.co for v in e.verts] for e in edges2]
    overlay = {}
    oget = overlay.get
    for i1, (a1, a2) in enumerate(aco):
        for i2, (b1, b2) in enumerate(bco):
            c1, c2 = a1.x, a2.x
            d1, d2 = b1.x, b2.x
            c1, c2 = (c1 - epsilon, c2) if c1 <= c2 else (c2 - epsilon, c1)
            d1, d2 = (d1 - epsilon, d2) if d1 <= d2 else (d2 - epsilon, d1)
            if c1 <= d2 and c2 >= d1:
                c1, c2 = a1.y, a2.y
                d1, d2 = b1.y, b2.y
                c1, c2 = (c1 - epsilon, c2) if c1 <= c2 else (c2 - epsilon, c1)
                d1, d2 = (d1 - epsilon, d2) if d1 <= d2 else (d2 - epsilon, d1)
                if c1 <= d2 and c2 >= d1:
                    c1, c2 = a1.z, a2.z
                    d1, d2 = b1.z, b2.z
                    c1, c2 = (c1 - epsilon, c2) if c1 <= c2 else (c2 - epsilon, c1)
                    d1, d2 = (d1 - epsilon, d2) if d1 <= d2 else (d2 - epsilon, d1)
                    if c1 <= d2 and c2 >= d1:
                        e1 = edges1[i1]
                        e2 = edges2[i2]
                        if e1 != e2:
                            overlay[e1] = oget(e1, set()).union({e2})
    return overlay

def intersect_edges_edges(overlay, precision = 4):
    epsilon = .1**precision
    fpre_min = -epsilon
    fpre_max = 1+epsilon
    splits = {}
    sp_get = splits.get
    new_edges1 = set()
    new_edges2 = set()
    targetmap = {}
    for edg1 in overlay:
        #print("***", ed1.index, "***")
        for edg2 in overlay[edg1]:
            #print('loop', ed2.index)
            a1 = edg1.verts[0]
            a2 = edg1.verts[1]
            b1 = edg2.verts[0]
            b2 = edg2.verts[1]
            
            # test if are linked
            if a1 in {b1, b2} or a2 in {b1, b2}:
                #print('linked')
                continue

            aco1, aco2 = a1.co, a2.co
            bco1, bco2 = b1.co, b2.co
            tp = intersect_line_line(aco1, aco2, bco1, bco2)
            if tp:
                p1, p2 = tp
                if (p1 - p2).to_tuple(precision) == (0,0,0):
                    v = aco2-aco1
                    f = p1 - aco1
                    x,y,z = abs(v.x), abs(v.y), abs(v.z)
                    max1 = 0 if x >= y and x >= z else\
                           1 if y >= x and y >= z else 2
                    fac1 = f[max1]/v[max1]

                    v = bco2-bco1
                    f = p2 - bco1
                    x,y,z = abs(v.x), abs(v.y), abs(v.z)
                    max2 = 0 if x >= y and x >= z else\
                           1 if y >= x and y >= z else 2
                    fac2 = f[max2]/v[max2]

                    if fpre_min <= fac1 <= fpre_max:
                        #print(edg1.index, 'can intersect', edg2.index)
                        ed1 = edg1
                        va1 = a1
                        va2 = a2

                    elif edg1 in splits:
                        for ed1 in splits[edg1]:
                            va1 = ed1.verts[0]
                            va2 = ed1.verts[1]

                            vco1 = va1.co
                            vco2 = va2.co

                            v = vco2-vco1
                            f = p1 - vco1
                            fac1 = f[max1]/v[max1]
                            if fpre_min <= fac1 <= fpre_max:
                                #print(e.index, 'can intersect', edg2.index)
                                break
                        else:
                            #print(edg1.index, 'really does not intersect', edg2.index)
                            continue
                    else:
                        #print(edg1.index, 'not intersect', edg2.index)
                        continue

                    if fpre_min <= fac2 <= fpre_max:
                        #print(ed1.index, 'actually intersect', edg2.index)
                        ed2 = edg2
                        vb1 = b1
                        vb2 = b2

                    elif edg2 in splits:
                        for ed2 in splits[edg2]:
                            vb1 = ed2.verts[0]
                            vb2 = ed2.verts[1]

                            vco1 = vb1.co
                            vco2 = vb2.co

                            v = vco2-vco1
                            f = p2 - vco1
                            fac2 = f[max2]/v[max2]
                            if fpre_min <= fac2 <= fpre_max:
                                #print(ed1.index, 'actually intersect', e.index)
                                break
                        else:
                            #print(ed1.index, 'really does not intersect', ed2.index)
                            continue
                    else:
                        #print(ed1.index, 'not intersect', edg2.index)
                        continue

                    new_edges1.add(ed1)
                    new_edges2.add(ed2)

                    if abs(fac1) <= epsilon:
                        nv1 = va1
                    elif fac1 + epsilon >= 1:
                        nv1 = va2
                    else:
                        ne1, nv1 = bmesh.utils.edge_split(ed1, va1, fac1)
                        new_edges1.add(ne1)
                        splits[edg1] = sp_get(edg1, set()).union({ne1})

                    if abs(fac2) <= epsilon:
                        nv2 = vb1
                    elif fac2 + epsilon >= 1:
                        nv2 = vb2
                    else:
                        ne2, nv2 = bmesh.utils.edge_split(ed2, vb1, fac2)
                        new_edges2.add(ne2)
                        splits[edg2] = sp_get(edg2, set()).union({ne2})

                    if nv1 != nv2: #necessary?
                        targetmap[nv1] = nv2
                #else:
                    #print('not coplanar')
            #else:
                #print("parallel or collinear")
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
            # edges to intersect
            edges = set()
            [[edges.add(ed) for ed in v.link_edges] for v in sface.verts]
            edges = list(edges)

            #edges to test intersect
            bm_edges = self.bm.edges

            overlay = edges_BVH_overlap(bm_edges, edges, epsilon = 0.0001)
            overlay = {k: v for k,v in overlay.items() if k not in edges} # remove repetition

            #print([e.index for e in edges])
            #for a, b in overlay.items():
                #print(a.index, [e.index for e in b])

            new_edges1, new_edges2, targetmap = intersect_edges_edges(overlay)
            pos_weld = set()
            for e in new_edges1:
                v1, v2 = e.verts
                if v1 in targetmap and v2 in targetmap:
                    pos_weld.add((targetmap[v1], targetmap[v2]))
            if targetmap:
                bmesh.ops.weld_verts(self.bm, targetmap=targetmap)
            #print([e.is_valid for e in new_edges1])
            #print([e.is_valid for e in new_edges2])
            for e in pos_weld:
                v1, v2 = e
                lf1 = set(v1.link_faces)
                lf2 = set(v2.link_faces)
                rlfe = lf1.intersection(lf2)
                for f in rlfe:
                    try:
                        bmesh.utils.face_split(f, v1, v2)
                    except:
                        pass
                
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
        self.cancel = event.type in {'ESC', 'NDOF_BUTTON_ESC'}
        self.confirm = event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}
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
