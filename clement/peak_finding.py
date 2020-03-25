import numpy as np
import scipy.ndimage as ndi
from scipy.optimize import curve_fit
import time
from skimage import measure, morphology
import read_lif


class Peak_finding():
    def __init__(self, threshold=0, plt=50, put=200):
        self.peaks_2d = None
        self.peaks_3d = None
        self.pixel_lower_threshold = plt
        self.pixel_upper_threshold = put
        self.flood_steps = 10
        self.threshold = threshold
        self.roi_min_size = 10

    def peak_finding(self, im, roi=False):
        start = time.time()
        img = np.copy(im)
        if self.threshold == 0:
            self.threshold = 0.1 * np.sort(img.ravel())[-100:].mean()
            print('Threshold: ', self.threshold)
        img[img < self.threshold] = 0

        labels, num_objects = ndi.label(img)
        label_size = np.bincount(labels.ravel())

        # single photons and no noise
        mask_sp = np.where((label_size >= self.pixel_lower_threshold) & (label_size < self.pixel_upper_threshold), True, False)
        if sum(mask_sp) == 0:
            coor_sp = []
        else:
            label_mask_sp = mask_sp[labels.ravel()].reshape(labels.shape)
            labels_sp = label_mask_sp * labels
            labels_sp, n_s = ndi.label(labels_sp)
            coor_sp = ndi.center_of_mass(img, labels_sp, range(1, labels_sp.max() + 1))

        # multiple photons
        mask_mp = np.where((label_size >= self.pixel_upper_threshold) & (label_size < np.max(label_size)), True, False)
        if sum(mask_mp) > 0:
            label_mask_mp = mask_mp[labels.ravel()].reshape(labels.shape)
            labels_mp = label_mask_mp * labels
            labels_mp, n_m = ndi.label(labels_mp)
            for i in range(1, sum(mask_mp) + 1):
                slice_x, slice_y = ndi.find_objects(labels_mp == i)[0]
                roi_i = np.copy(img[slice_x, slice_y])
                max_i = np.max(roi_i)
                step = (0.95*max_i - self.threshold) / self.flood_steps
                multiple = False
                coor_tmp = np.array(ndi.center_of_mass(roi_i, ndi.label(roi_i)[0]))
                for k in range(1, self.flood_steps + 1):
                    new_threshold = self.threshold + k * step
                    roi_i[roi_i < new_threshold] = 0
                    labels_roi, n_i = ndi.label(roi_i)
                    if n_i > 1:
                        roi_label_size = np.bincount(labels_roi.ravel())
                        if (np.max(roi_label_size[1:]) <= self.pixel_upper_threshold):  # if label_size == self.pixel_upper_threshold + 1 and is single hit not multiple
                            if len(roi_label_size) == 3 and roi_label_size.min() < self.roi_min_size:
                                break
                            else:
                                multiple = True
                                # print('multiple hits!')
                                coordinates_roi = np.array(ndi.center_of_mass(roi_i, labels_roi, range(1, n_i + 1)))
                                [coor_sp.append(coordinates_roi[j] + np.array((slice_x.start, slice_y.start))) for j in
                                 range(len(coordinates_roi))]
                                break
                if not multiple:
                    coor_sp.append(coor_tmp + np.array((slice_x.start, slice_y.start)))
                    coor_sp.append(coor_tmp + np.array((slice_x.start, slice_y.start)))

        coor = np.array(coor_sp)
        if roi:
            return np.round(coor)
        else:
            self.peaks_2d = np.round(coor)
        end = time.time()
        print('duration: ', end-start)
        print('Number of peaks found: ', self.peaks_2d.shape[0])


    def wshed_peaks(self, img):
        if self.threshold == 0:
            self.threshold = 0.1 * np.sort(img.ravel())[-100:].mean()
        print(self.threshold)
        labels = morphology.label(img >= self.threshold, connectivity=1)
        morphology.remove_small_objects(labels, self.pixel_lower_threshold, connectivity=1, in_place=True)
        wshed = morphology.watershed(-img * (labels > 0), labels)
        self.peaks_2d = np.round(np.array([r.weighted_centroid for r in measure.regionprops((labels > 0) * wshed, img)]))


    def calc_z_position(self, data):
        gauss = lambda x, a, mu, sigma : a * np.exp(-(x-mu)**2 / (2*sigma**2))
        z_profile = data[self.peaks_2d[:, 0].astype(int), self.peaks_2d[:, 1].astype(int)]
        z_max = np.argmax(z_profile, axis=1)
        z_shifted = np.zeros((z_profile.shape[0], z_profile.shape[1]*2))
        x = np.arange(z_shifted.shape[1])
        mean_values = np.zeros((z_shifted.shape[0],1))
        shifts = []
        go = time.time()
        for i in range(z_profile.shape[0]):
            start = z_profile.shape[1] - z_max[i]
            shifts.append(start)
            stop = start + z_profile.shape[1]
            z_shifted[i, start:stop] = (z_profile[i,:] - z_profile[i,:].min()) / (z_profile[i,:].max() - z_profile[i,:].min())
            for k in range(z_shifted.shape[1]):
                if z_shifted[i, k] == 0:
                    z_shifted[i, k] = z_shifted[i, -k]
        z_avg = z_shifted.mean(0)
        popt, pcov = curve_fit(gauss, x, z_avg, p0=[1, 31, 1])
        gauss_stat = lambda x, mu : popt[0] * np.exp(-(x-mu)**2 / (2*popt[2]**2))
        for i in range(z_shifted.shape[0]):
            popt_i, pcov_i = curve_fit(gauss_stat, x, z_shifted[i], p0=popt[1])
            mean_values[i] = popt_i[0]-shifts[i]
        print(mean_values)
        self.peaks_3d = np.concatenate((self.peaks_2d, mean_values), axis=1)

        no = time.time()
        print('Duration:', no-go)


if __name__ == '__main__':
    from matplotlib import pyplot as plt
    plt.ion()
    fname = '/home/tamme/phd/Clement/data/3D/grid1_05.lif'

    base_reader = read_lif.Reader(fname)
    reader = base_reader.getSeries()[0]

    num_slices = reader.getFrameShape()[0]
    num_channels = len(reader.getChannels())

    max_proj = np.array(reader.getFrame(channel=3, dtype='u2').max(2).astype('f4'))
    t_max = np.sort(max_proj.ravel())[-100:].mean()

    peaks = Peak_finding(threshold=0.1*t_max)
    peaks.peak_finding(max_proj)
    print(peaks.peaks_2d.shape)

    plt.figure()
    plt.imshow(max_proj)
    plt.scatter(peaks.peaks_2d[:,1], peaks.peaks_2d[:,0], facecolor=None, edgecolor='r')
    plt.show()