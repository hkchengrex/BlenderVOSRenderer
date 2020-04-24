import bpy, bmesh
import numpy as np
import scipy
import scipy.cluster
import random
import math
import mathutils
import itertools
from sklearn.cluster import KMeans, SpectralClustering
from collections import defaultdict
from scipy.spatial.transform import Rotation
import numpy.polynomial.polynomial as poly


def _face_center(mesh, face):
    """Computes the coordinates of the center of the given face"""
    center = mathutils.Vector()
    for vert in face.vertices:
        center += mesh.vertices[vert].co
    return center/len(face.vertices)

def _insert_symmetric(A, rowA, colA, i, j, val):
    A.append(val)
    rowA.append(i)
    colA.append(j)
    A.append(val)
    rowA.append(j)
    colA.append(i)

class Node:
    def __init__(self, managed, Vs, Ws, r=None, t=None):

        self.managed = managed
        self.Vs = Vs.copy()
        self.Ws = Ws.copy()[:, None]

        # In frame of parent
        if r is None:
            self.r = Rotation.from_euler('zyx', np.zeros(3))
        else:
            self.r = r
        if t is None:
            self.t = np.zeros(3)
        else:
            self.t = t
        self.child = []

        # Parent, *local = global
        self.pr = Rotation.from_euler('zyx', np.zeros(3))
        self.pt = np.zeros(3)

        self.true_r = None
        self.true_t = None

    def add_joint(self, joint):
        self.Vs -= joint

    def propagate(self):
        # self.true_r = self.r * self.pr
        # self.true_t = self.r.apply(self.pt) + self.t
        self.true_r = self.pr * self.r

        angle = self.true_r.as_euler('zxy')
        self.true_r = Rotation.from_euler('zxy', np.clip(angle, -np.pi, np.pi))

        self.true_t = self.pr.apply(self.t) + self.pt
        for c in self.child:
            c.pr = self.true_r
            c.pt = self.true_t
            c.propagate()

    def apply_all(self):
        return self.true_r.apply(self.Vs) + self.true_t
    

class MeshModeler:
    def __init__(self, mesh, k):
        self.mesh = mesh
        self.k = k
        self.n_faces = len(self.mesh.polygons)
        self.n_vert = len(self.mesh.vertices)

        self.verts = np.empty(self.n_vert*3, dtype=np.float64)
        mesh.vertices.foreach_get('co', self.verts)
        self.verts.shape = (self.n_vert, 3)
        self.verts = self.verts.astype(np.float32)

        self.origin = np.zeros(3, dtype=np.float32)

        print('mesh_modeler: Number of faces: ', self.n_faces)

        self.get_adj_faces()

    def get_adj_faces(self):
        # map from edge-key to adjacent faces
        self.adj_faces_map = {}
        # find adjacent faces by iterating edges
        for index, face in enumerate(self.mesh.polygons):
            if face.normal.magnitude < 1e-6:
                # Happens fpr some models? What do you even mean by a zero normal?
                continue
            for edge in face.edge_keys:
                if edge in self.adj_faces_map:
                    self.adj_faces_map[edge].append(index)
                else:
                    self.adj_faces_map[edge] = [index]

    def segment_mesh(self):
        # Cluster the faces
        print("mesh_segmentation: Assigning face positions...")
        self.face_loc = np.empty((self.n_faces, 3), dtype=np.float32)
        for i, f in enumerate(self.mesh.polygons):
            self.face_loc[i,:] = _face_center(self.mesh, f)

        print("mesh_segmentation: Running K-Means with K=%d..." % self.k)
        kmeans = KMeans(n_clusters=self.k, n_init=1).fit(self.face_loc)
        labels = kmeans.labels_

        print("mesh_segmentation: Finding connected components...")
        Crow, Ccol, Cval = [], [], []
        for _, adj_faces in self.adj_faces_map.items():
            for i, j in itertools.combinations(adj_faces, 2):
                if labels[i] == labels[j]:
                    # Connected
                    _insert_symmetric(Cval, Crow, Ccol, i, j, 1)
        C = scipy.sparse.csr_matrix((Cval, (Crow, Ccol)), shape=(self.n_faces, self.n_faces))
        n_components, new_labels = scipy.sparse.csgraph.connected_components(C, directed=False)

        # Eliminate small components
        new_centroids = {}
        for i in range(n_components):
            idx = new_labels==i
            if (idx).sum() < 10:
                new_labels[idx] = -1
            else:
                new_centroids[i] = self.face_loc[idx].mean(0)

        for i, l in enumerate(new_labels):
            if l == -1:
                min_dist = np.inf
                min_cidx = 0
                for cidx, cpos in new_centroids.items():
                    dist = np.linalg.norm(cpos-self.face_loc[i])
                    if dist < min_dist:
                        min_dist = dist
                        min_cidx = cidx
                new_labels[i] = min_cidx

        re_labels = new_labels.copy()
        self.centroid = {}
        new_components = np.unique(new_labels)
        for i, j in enumerate(new_components):
            re_labels[new_labels==j] = i
            self.centroid[i] = new_centroids[j]
        n_new_components = len(new_components)
        
        print("mesh_segmentation: Eliminated small components from %d to %d" % (n_components, n_new_components))


        print("mesh_segmentation: Done clustering! Number of labels: %d" % n_new_components)
        self.nc = n_new_components
        self.mesh_seg_idx = re_labels

    def _find_joints(self):
        connections = np.zeros((self.nc, self.nc), dtype=np.uint8)
        splitting_edges = defaultdict(list)

        for edge, adj_faces in self.adj_faces_map.items():
            types = set([self.mesh_seg_idx[f] for f in adj_faces])
            # Loop through all combinations of clusters, usually just 2
            # Sorted to maintain relative order
            for i, j in itertools.combinations(sorted(types), 2):
                connections[i,j] = connections[j,i] = 1
                splitting_edges[(i,j)].append(edge)

        joints = defaultdict(list)
        for k, edges in splitting_edges.items():
            v_sum = np.zeros(3, dtype=np.float32)
            for e in edges:
                v_sum += self.mesh.vertices[e[0]].co
            v_sum /= len(edges)
            joints[k] = v_sum

        self.joints = joints
        return connections

    def _build_tree(self, connection):
        # Start with a forest
        tree = {}
        for k in self.centroid.keys():
            tree[k] = []

        # find a root node
        min_dist = np.inf
        min_node = None
        for k, j in self.centroid.items():
            dist = np.linalg.norm(j - self.origin)
            if dist < min_dist:
                min_dist = dist
                min_node = k
        root = min_node

        inserted = [root]
        # We need to perform multiple passes, to minimize the tree depth
        tree_extended = True
        while tree_extended:
            buffer_inserted = inserted.copy()
            tree_extended = False
            for i in range(self.nc):
                if i not in buffer_inserted:
                    for j in buffer_inserted:
                        if connection[i][j] > 0.5:
                            # Connect and build tree
                            inserted.append(i)
                            tree[j].append(i)
                            tree_extended = True
                            break


        # Merge the segments that are not connected to the tree by their nearest neighbor
        for i in range(self.nc):
            if i not in inserted:
                # Is lonely
                min_dist = np.inf
                min_node = None
                for j in inserted:
                    dist = np.linalg.norm(self.centroid[i] - self.centroid[j])
                    if dist < min_dist:
                        min_dist = dist
                        min_node = j
                self.mesh_seg_idx[self.mesh_seg_idx==i] = -1

        # Reinstate the cluster numbering
        buf_label = self.mesh_seg_idx.copy()
        buf_centr = {}
        new_tree = {}
        new_components = np.unique(self.mesh_seg_idx)
        new_components = np.delete(new_components, np.where(new_components == -1))

        replacement = {}
        for i, j in enumerate(new_components):
            buf_label[self.mesh_seg_idx==j] = i
            buf_centr[i] = self.centroid[j]
            new_tree[i] = [m for m, n in enumerate(new_components) if n in tree[j]]
            replacement[j] = i

        # Replace the joints
        buf_joints = {}
        for i, j in self.joints.keys():
            if i not in replacement or j not in replacement:
                # The connection is not present in the new clusters
                continue
            m = replacement[i]
            n = replacement[j]
            buf_joints[tuple(sorted([m,n]))] = self.joints[(i,j)]
        
        print("build_skeleton: Eliminated lonely components from %d to %d" % (self.nc, len(new_components)))
        print("build_skeleton: Eliminated joints from %d to %d" % (len(self.joints), len(buf_joints)))
        self.joints = buf_joints
        self.nc = len(new_components)
        self.mesh_seg_idx = buf_label
        self.centroid = buf_centr
        self.tree = new_tree
        self.root = replacement[root]

    def _compute_weight_map(self):
        # Compute weight map
        weight = np.zeros((self.n_vert, self.nc))
        for f, id in enumerate(self.mesh_seg_idx):
            weight[self.mesh.polygons[f].vertices, id] += 1
        self.weight_map = weight / (weight.sum(1, keepdims=True) + 1e-9)

    def _solve_node_one_step(self, parent, parent_joint):
        for child in self.tree[parent]:
            key = tuple(sorted([child, parent]))
            joint = self.joints[key]
            self.nodes[parent].child.append(self.nodes[child])
            self.nodes[child].t = joint - parent_joint
            self.nodes[child].add_joint(joint)
            self._solve_node_one_step(child, joint)

    def _compute_hierarchical_model(self):
        self.nodes = []
        for i in range(self.nc):
            managed = self.weight_map[:, i] > 1e-5
            Vs = self.verts[managed, :]
            Ws = self.weight_map[managed, i]
            self.nodes.append(Node(managed, Vs, Ws))
        
        self.nodes[self.root].t = self.centroid[self.root]
        self.nodes[self.root].add_joint(self.centroid[self.root])
        self._solve_node_one_step(self.root, self.centroid[self.root])

        self.nodes[self.root].propagate()

    def build_skeleton(self):
        # find edges that are touching faces from different segments
        connections = self._find_joints()
        print('build_skeleton: %d connections found...' % connections.sum())

        print('build_skeleton: building joint tree...')
        self._build_tree(connections)

        print('build_skeleton: computing vertex weight map...')
        self._compute_weight_map()

        print('build_skeleton: computing hierarchical model...')
        self._compute_hierarchical_model()

        print('build_skeleton: Skeleton completed!')

    def build_animation(self, n_frames):
        print('build_animation: Starting...')

        self.node_poly = {}
        self.n_frames = n_frames
        for i in range(len(self.nodes)):
            if i == self.root:
                continue
            degree = np.random.randint(3, 7)
            rot_angles = np.zeros((degree+1, 3))
            max_angle_diff = 0.1 * n_frames / degree

            rot_angles[0] = np.zeros(3)
            for j in range(1, degree+1):
                this_ang_dist = np.random.rand(3) * max_angle_diff
                rot_angles[j] = rot_angles[j-1] + this_ang_dist
                rot_angles[j] = np.clip(rot_angles[j], -np.pi/4, np.pi/4)
            Xs = np.array([k/degree for k in range(degree+1)])
            self.node_poly[i] = poly.polyfit(Xs, rot_angles, deg=degree)


    def update_animation(self, frame_i):
        for i in range(len(self.nodes)):
            if i == self.root:
                continue
            angle = poly.polyval(frame_i/self.n_frames, self.node_poly[i])
            self.nodes[i].r = Rotation.from_euler('zxy', angle)

    # def mod_rotation(self, n_f):
    #     for n in self.nodes:
    #         if n == self.nodes[self.root]:
    #             continue
    #         # angle = n.r.as_euler('zyx')
    #         angle = np.zeros(3, dtype=np.float32)
    #         angle = np.clip(angle+n_f*0.02, -np.pi/2, np.pi/2)
    #         n.r = Rotation.from_euler('zyx', angle)

    def apply_transformation(self):
        self.nodes[self.root].propagate()
        Vs = np.zeros_like(self.verts)
        for n in self.nodes:
            up_v = n.apply_all()
            Vs[n.managed,:] += up_v * n.Ws
        for i, v in enumerate(self.mesh.vertices):
            v.co = Vs[i,:]

        self.mesh.update()
