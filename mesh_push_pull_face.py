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

import bpy, bmesh
from mathutils.geometry import intersect_line_line
from bpy.props import FloatProperty

class BVHco():
    i = 0
    c1x = 0
    c1y = 0
    c1z = 0
    c2x = 0
    c2y = 0
    c2z = 0
    
def edges_BVH_overlap(bm, edges2, epsilon = 0.0001):
    bco = set()
    for e in edges2:
        bvh = BVHco()
        bvh.i = e.index
        b1 = e.verts[0]
        b2 = e.verts[1]
        co1 = b1.co.x
        co2 = b2.co.x
        if co1 <= co2:
            bvh.c1x = co1 - epsilon
            bvh.c2x = co2
        else:
            bvh.c1x = co2 - epsilon
            bvh.c2x = co1
        co1 = b1.co.y
        co2 = b2.co.y
        if co1 <= co2:
            bvh.c1y = co1 - epsilon
            bvh.c2y = co2
        else:
            bvh.c1y = co2 - epsilon
            bvh.c2y = co1
        co1 = b1.co.z
        co2 = b2.co.z
        if co1 <= co2:
            bvh.c1z = co1 - epsilon
            bvh.c2z = co2
        else:
            bvh.c1z = co2 - epsilon
            bvh.c2z = co1
        bco.add(bvh)
    del edges2
    overlay = {}
    for e1 in bm.edges:
        by = bz = True
        a1 = e1.verts[0]
        a2 = e1.verts[1]
        c1x = a1.co.x
        c2x = a2.co.x
        if c1x <= c2x:
            c1x -= epsilon
        else:
            tm = c1x
            c1x = c2x - epsilon
            c2x = tm
        for bvh in bco:
            d1 = bvh.c1x
            d2 = bvh.c2x
            if c1x <= d2 and c2x >= d1:
                if by:
                    by = False
                    c1y = a1.co.y
                    c2y = a2.co.y
                    if c1y <= c2y:
                        c1y -= epsilon
                    else:
                        tm = c1y
                        c1y = c2y - epsilon
                        c2y = tm
                d1 = bvh.c1y
                d2 = bvh.c2y
                if c1y <= d2 and c2y >= d1:
                    if bz:
                        bz = False
                        c1z = a1.co.z
                        c2z = a2.co.z
                        if c1z <= c2z:
                            c1z -= epsilon
                        else:
                            tm = c1z
                            c1z = c2z - epsilon
                            c2z = tm
                    d1 = bvh.c1z
                    d2 = bvh.c2z
                    if c1z <= d2 and c2z >= d1:
                        e2 = bm.edges[bvh.i]
                        if e1 != e2:
                            overlay[e1] = overlay.get(e1, set()).union({e2})
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

                    elif edg1 in splits:
                        for ed1 in splits[edg1]:
                            a1 = ed1.verts[0]
                            a2 = ed1.verts[1]

                            vco1 = a1.co
                            vco2 = a2.co

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

                    elif edg2 in splits:
                        for ed2 in splits[edg2]:
                            b1 = ed2.verts[0]
                            b2 = ed2.verts[1]

                            vco1 = b1.co
                            vco2 = b2.co

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
                        nv1 = a1
                    elif fac1 + epsilon >= 1:
                        nv1 = a2
                    else:
                        ne1, nv1 = bmesh.utils.edge_split(ed1, a1, fac1)
                        new_edges1.add(ne1)
                        splits[edg1] = sp_get(edg1, set()).union({ne1})

                    if abs(fac2) <= epsilon:
                        nv2 = b1
                    elif fac2 + epsilon >= 1:
                        nv2 = b2
                    else:
                        ne2, nv2 = bmesh.utils.edge_split(ed2, b1, fac2)
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

            overlay = edges_BVH_overlap(self.bm, edges, epsilon = 0.0001)
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
            #sp_faces1 = set()
            for e in pos_weld:
                v1, v2 = e
                lf1 = set(v1.link_faces)
                lf2 = set(v2.link_faces)
                rlfe = lf1.intersection(lf2)
                for f in rlfe:
                    try:
                        nf = bmesh.utils.face_split(f, v1, v2)
                        #sp_faces1.update({f, nf[0]})
                    except:
                        pass

            #sp_faces2 = set()
            for e in new_edges2:
                lfe = set(e.link_faces)
                v1, v2 = e.verts
                lf1 = set(v1.link_faces)
                lf2 = set(v2.link_faces)
                rlfe = lf1.intersection(lf2)
                for f in rlfe.difference(lfe):
                    nf = bmesh.utils.face_split(f, v1, v2)
                    #sp_faces2.update({f, nf[0]})

            #print([f.index for f in sp_faces1])
            #print([f.index for f in sp_faces2])
            '''print([e.index for e in sface.edges])
            normal = (-sface.normal).to_tuple(5)
            for e in sface.edges:
                if e.calc_face_angle(0) < 0.01:
                    print(len(e.link_faces))
                    for f in e.link_faces:
                        if f != sface and\
                            (f.normal.to_tuple(5) == normal or\
                            (-f.normal).to_tuple(5) == normal):
                                sface.copy_from_face_interp(f, True)
                                break'''
                
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
        #from mathutils.bvhtree import BVHTree
        #t = time.time()
        #BVHTree.FromBMesh(self.bm, epsilon=0.0)
        #print(time.time()-t)
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
