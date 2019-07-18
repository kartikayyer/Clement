import sys
import glob
import os
import numpy as np
import scipy.signal as sc
import mrcfile as mrc
#import pyqtgraph as pg
import matplotlib
import scipy.ndimage as ndi
from skimage import transform as tf
from matplotlib import pyplot as plt
matplotlib.use('QT5Agg')

class Assembler():
    def __init__(self, step=100):
        self.step = int(np.sqrt(step))
        self.orig_data = None
        self.data = None
        self.backup = None
        self.transformed_data = None   
        self.pos_x = None
        self.pos_y = None
        self.pos_z = None
        self._tf_data = None
        self.tf_matrix = np.identity(3)

    def parse(self, fname):
        with mrc.open(fname, 'r', permissive=True) as f:
            try:
                self.orig_data = f.data[:,::self.step,::self.step]
            except IndexError:
                self.orig_data = f.data
            self._h = f.header
            self._eh = np.frombuffer(f.extended_header, dtype='i2')

    def assemble(self):
        dimensions = self.orig_data.shape
        
        if len(dimensions) == 3:
            self.pos_x = self._eh[1:10*dimensions[0]:10] // self.step
            self.pos_y = self._eh[2:10*dimensions[0]:10] // self.step
            self.pos_z = self._eh[3:10*dimensions[0]:10]

            cy, cx = np.indices(dimensions[1:3])

            self.data = np.zeros((np.max(self.pos_x)+dimensions[2],np.max(self.pos_y)+dimensions[1]), dtype='f4')
            #sys.stderr.write(self.data.shape)

            self.mcounts = np.zeros_like(self.data)
            for i in range(dimensions[0]):
                sys.stderr.write('\rMerge for image {}'.format(i))
                np.add.at(self.mcounts, (cx+self.pos_x[i], cy+self.pos_y[i]), 1)
                np.add.at(self.data, (cx+self.pos_x[i], cy+self.pos_y[i]), self.orig_data[i])
            sys.stderr.write('\n')

            self.data[self.mcounts>0] /= self.mcounts[self.mcounts>0]
        else:
            self.data = np.copy(self._stack_data)

        self._orig_data = np.copy(self.data)

    def save_merge(self, fname):
        with mrc.new(fname, overwrite=True) as f:
            f.set_data(self.data)
            f.update_header_stats()

    def toggle_original(self, transformed=None):
        if self._tf_data is None:
            print('Need to transform data first')
            return
        if transformed is None:
            self.data = np.copy(self._tf_data if self.transformed else self._orig_data)
            self.transformed = not self.transformed
        else:
            self.transformed = transformed
            self.data = np.copy(self._tf_data if self.transformed else self._orig_data)

    def calc_transform(self, my_points):
        print('Input points:\n', my_points)
        side_list = np.linalg.norm(np.diff(my_points, axis=0), axis=1)
        side_list = np.append(side_list, np.linalg.norm(my_points[0] - my_points[-1]))

        side_length = np.mean(side_list)
        print('ROI side length:', side_length, '\xb1', side_list.std())

        cen = my_points.mean(0) - np.ones(2)*side_length/2.
        self.new_points = np.zeros_like(my_points)
        self.new_points[0] = cen + (0, 0)
        self.new_points[1] = cen + (side_length, 0)
        self.new_points[2] = cen + (side_length, side_length)
        self.new_points[3] = cen + (0, side_length)

        self.tf_matrix = tf.estimate_transform('affine', my_points[:4], self.new_points).params

        nx, ny = self.data.shape
        corners = np.array([[0, 0, 1], [nx, 0, 1], [nx, ny, 1], [0, ny, 1]]).T
        self.tf_corners = np.dot(self.tf_matrix, corners)
        self._tf_shape = tuple([int(i) for i in (self.tf_corners.max(1) - self.tf_corners.min(1))[:2]])
        self.tf_matrix[:2, 2] -= self.tf_corners.min(1)[:2]
        print('Transform matrix:\n', self.tf_matrix)
        self.apply_transform()

    def apply_transform(self):
        if self.tf_matrix is None:
            print('Calculate transform matrix first')
            return
        self._tf_data = ndi.affine_transform(self.data, np.linalg.inv(self.tf_matrix), order=1, output_shape=self._tf_shape)
        self.transform_shift = -self.tf_corners.min(1)[:2]
        print(self._tf_data.shape, self.transform_shift)
        self.transformed = True
        self.data = np.copy(self._tf_data)
        self.new_points = np.array([point + self.transform_shift for point in self.new_points])

if __name__=='__main__':
    path = '../gs.mrc'
    assembler = Assembler()
    assembler.parse(path)
    assembler.assemble()
    #pg.show(merged.T)
