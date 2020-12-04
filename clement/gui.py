#!/usr/bin/env python
import sys
import os
import warnings
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from . import res_styles
from .sem_controls import SEMControls
from .tem_controls import TEMControls
from .fm_controls import FMControls
from .fib_controls import FIBControls
from .project import Project
from .popup import Merge, Scatter, Convergence, Peak_Params
from . import utils

warnings.simplefilter('ignore', category=FutureWarning)

def resource_path(rel_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, rel_path)


class GUI(QtWidgets.QMainWindow):
    def __init__(self, project_fname=None, no_restore=False):
        super(GUI, self).__init__()
        if not no_restore:
            self.settings = QtCore.QSettings('MPSD-CNI', 'CLEMGui', self)
        else:
            self.settings = QtCore.QSettings()
        self.colors = self.settings.value('channel_colors', defaultValue=['#ff0000', '#00ff00', '#0000ff', '#808080', '#808080'])
        self._init_ui()
        if project_fname is not None:
            self.project._load_project(project_fname)

    def _init_ui(self):
        geom = self.settings.value('geometry')
        if geom is None:
            self.resize(1600, 800)
        else:
            self.setGeometry(geom)

        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        # Image views
        splitter_images = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        layout.addWidget(splitter_images, stretch=1)

        # -- FM Image view
        # self.fm_imview = pg.ImageView()
        self.fm_stacked_imview = QtWidgets.QStackedWidget()
        self.fm_imview = pg.ImageView()
        self.fm_imview.ui.roiBtn.hide()
        self.fm_imview.ui.menuBtn.hide()
        self.fm_stacked_imview.addWidget(self.fm_imview)
        self.fm_stacked_imview.addWidget(self.fm_imview)
        splitter_images.addWidget(self.fm_stacked_imview)

        # -- EM Image view
        self.em_imview = QtWidgets.QStackedWidget()
        self.sem_imview = pg.ImageView()
        self.sem_imview.ui.roiBtn.hide()
        self.sem_imview.ui.menuBtn.hide()
        self.fib_imview = pg.ImageView()
        self.fib_imview.ui.roiBtn.hide()
        self.fib_imview.ui.menuBtn.hide()
        self.tem_imview = pg.ImageView()
        self.tem_imview.ui.roiBtn.hide()
        self.tem_imview.ui.menuBtn.hide()
        self.em_imview.addWidget(self.sem_imview)
        self.em_imview.addWidget(self.fib_imview)
        self.em_imview.addWidget(self.tem_imview)
        splitter_images.addWidget(self.em_imview)

        # Options
        options = QtWidgets.QHBoxLayout()
        options.setContentsMargins(4, 0, 4, 4)
        layout.addLayout(options)

        merge_options = QtWidgets.QHBoxLayout()
        merge_options.setContentsMargins(4, 0, 4, 4)
        layout.addLayout(merge_options)

        print_layout = QtWidgets.QHBoxLayout()
        print_layout.setContentsMargins(4, 0, 4, 4)
        layout.addLayout(print_layout)
        self.print_label = QtWidgets.QLabel('')
        print_layout.addWidget(self.print_label)
        print_layout.addStretch(1)
        self.worker = utils.PrintGUI(self.print_label)
        self.workerThread = QtCore.QThread()
        self.workerThread.started.connect(self.worker.run)
        self.worker.moveToThread(self.workerThread)
        self.print = self.worker.print
        self.log = self.worker.log
        self.workerThread.start()

        vbox = QtWidgets.QVBoxLayout()
        self.tabs = QtWidgets.QTabWidget()
        tab_sem = QtWidgets.QWidget()
        tab_fib = QtWidgets.QWidget()
        tab_tem = QtWidgets.QWidget()
        self.tabs.resize(300, 200)
        self.tabs.addTab(tab_sem, 'SEM')
        self.tabs.addTab(tab_fib, 'FIB')
        self.tabs.addTab(tab_tem, 'TEM')
        vbox.addWidget(self.tabs)

        self.vbox_sem = QtWidgets.QVBoxLayout()
        self.vbox_fib = QtWidgets.QVBoxLayout()
        self.vbox_tem = QtWidgets.QVBoxLayout()
        tab_sem.setLayout(self.vbox_sem)
        tab_fib.setLayout(self.vbox_fib)
        tab_tem.setLayout(self.vbox_tem)

        self.sem_controls = SEMControls(self.sem_imview, self.vbox_sem, merge_options, self.print, self.log)
        self.sem_imview.getImageItem().getViewBox().sigRangeChanged.connect(self.sem_controls._couple_views)
        self.sem_controls.curr_folder = self.settings.value('sem_folder', defaultValue=os.getcwd())
        self.vbox_sem.addWidget(self.sem_controls)
        self.fib_controls = FIBControls(self.fib_imview, self.vbox_fib, self.sem_controls.ops, merge_options, self.print, self.log)
        self.fib_controls.curr_folder = self.settings.value('fib_folder', defaultValue=os.getcwd())
        self.vbox_fib.addWidget(self.fib_controls)
        self.tem_controls = TEMControls(self.tem_imview, self.vbox_tem, merge_options, self.print, self.log)
        self.tem_imview.getImageItem().getViewBox().sigRangeChanged.connect(self.tem_controls._couple_views)
        self.tem_controls.curr_folder = self.settings.value('tem_folder', defaultValue=os.getcwd())
        self.vbox_tem.addWidget(self.tem_controls)


        self.fm_controls = FMControls(self.fm_imview, self.colors, merge_options, self.print, self.log)
        self.fm_imview.getImageItem().getViewBox().sigRangeChanged.connect(self.fm_controls._couple_views)
        self.fm_controls.curr_folder = self.settings.value('fm_folder', defaultValue=os.getcwd())
        options.addWidget(self.fm_controls)
        options.addLayout(vbox)

        self.tabs.currentChanged.connect(self.select_tab)
        # Connect controllers
        self.fm_controls.err_plt_btn.clicked.connect(lambda: self._show_scatter(idx=self.tabs.currentIndex()))
        self.fm_controls.convergence_btn.clicked.connect(lambda: self._show_convergence(idx=self.tabs.currentIndex()))
        self.fm_controls.set_params_btn.clicked.connect(lambda: self._show_peak_params())
        self.sem_controls.other = self.fm_controls
        self.fib_controls.other = self.fm_controls
        self.tem_controls.other = self.fm_controls
        self.fm_controls.other = self.sem_controls
        self.fm_controls.merge_btn.clicked.connect(self.merge)

        self.sem_popup = None
        self.fib_popup = None
        self.tem_popup = None
        self.scatter = None
        self.convergence = None
        self.peak_params = None
        self.project = Project(self.fm_controls, self.sem_controls, self.fib_controls, self.tem_controls, self, self.print, self.log)
        self.project._project_folder = self.settings.value('project_folder', defaultValue=os.getcwd())
        # Menu Bar
        self._init_menubar()

        self.theme = self.settings.value('theme')
        if self.theme is None:
            self.theme = 'none'
        self._set_theme(self.theme)

        self.show()

    def _init_menubar(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        # -- File menu
        filemenu = menubar.addMenu('&File')
        action = QtWidgets.QAction('Load &FM image(s)', self)
        action.triggered.connect(self.fm_controls._load_fm_images)
        filemenu.addAction(action)
        action = QtWidgets.QAction('Load SEM', self)
        action.triggered.connect(lambda idx: self.load_and_select_tab(idx=0))
        filemenu.addAction(action)
        action = QtWidgets.QAction('Load FIB', self)
        action.triggered.connect(lambda idx: self.load_and_select_tab(idx=1))
        filemenu.addAction(action)
        action = QtWidgets.QAction('Load TEM', self)
        action.triggered.connect(lambda idx: self.load_and_select_tab(idx=2))
        filemenu.addAction(action)
        action = QtWidgets.QAction('Load project', self)
        action.triggered.connect(self._load_p)
        filemenu.addAction(action)
        action = QtWidgets.QAction('Save project', self)
        action.triggered.connect(self._save_p)
        filemenu.addAction(action)
        #action = QtWidgets.QAction('&Save binned montage', self)
        #action.triggered.connect(self.sem_controls._save_mrc_montage)
        filemenu.addAction(action)
        action = QtWidgets.QAction('&Quit', self)
        action.triggered.connect(self.close)
        filemenu.addAction(action)

        # -- Theme menu
        thememenu = menubar.addMenu('&Theme')
        agroup = QtWidgets.QActionGroup(self)
        agroup.setExclusive(True)
        # action = QtWidgets.QAction('None', self)
        # action.triggered.connect(lambda: self._set_theme('none'))
        # thememenu.addAction(action)
        # agroup.addAction(action)
        action = QtWidgets.QAction('Dark', self)
        action.triggered.connect(lambda: self._set_theme('dark'))
        thememenu.addAction(action)
        agroup.addAction(action)
        action = QtWidgets.QAction('Solarized', self)
        action.triggered.connect(lambda: self._set_theme('solarized'))
        thememenu.addAction(action)
        agroup.addAction(action)

        self.show()

    def _save_p(self):
        self.project._save_project()

    def _load_p(self):
        self.project._load_project()

    def load_and_select_tab(self, idx):
        if idx == 0:
            self.sem_controls._load_mrc()
        elif idx == 1:
            self.fib_controls._load_mrc()
        else:
            self.tem_controls._load_mrc()
        self.tabs.setCurrentIndex(idx)

    @utils.wait_cursor('print')
    def select_tab(self, idx):
        self.fm_controls.select_btn.setChecked(False)
        for i in range(len(self.fm_controls._points_corr)):
            self.fm_controls._remove_correlated_points(self.fm_controls._points_corr[0])
        self.em_imview.setCurrentIndex(idx)
        self.sem_controls.tab_index = idx
        self.fib_controls.tab_index = idx
        self.tem_controls.tab_index = idx
        if idx == 0:
            self.fib_controls.show_grid_btn.setChecked(False)
            self.sem_controls._update_imview()
            self.fm_controls.other = self.sem_controls
            if self.sem_controls._refined:
                self.fm_controls.undo_refine_btn.setEnabled(True)
            else:
                self.fm_controls.undo_refine_btn.setEnabled(False)
        elif idx == 1:
            if self.sem_controls.ops is not None and self.fm_controls.ops is not None:
                if self.fm_controls.ops.points is not None and self.sem_controls.ops.points is not None:
                    self.fm_controls._calc_tr_matrices()
            if self.fib_controls.ops is not None:
                show_grid = self.sem_controls.show_grid_btn.isChecked()
                self.fib_controls.show_grid_btn.setChecked(show_grid)
            if self.fib_controls._refined:
                self.fm_controls.undo_refine_btn.setEnabled(True)
            else:
                self.fm_controls.undo_refine_btn.setEnabled(False)
            self.fib_controls._update_imview()
            self.fib_controls.sem_ops = self.sem_controls.ops
            self.fm_controls.other = self.fib_controls
            if self.sem_controls.ops is not None:
                if self.sem_controls.ops._orig_points is not None:
                    self.fib_controls.enable_buttons(enable=True)
                else:
                    self.fib_controls.enable_buttons(enable=False)
                if self.fib_controls.ops is not None and self.sem_controls.ops._tf_points is not None:
                    self.fib_controls.ops._transformed = True
        else:
            self.fib_controls.show_grid_btn.setChecked(False)
            self.tem_controls._update_imview()
            self.fm_controls.other = self.tem_controls
            if self.tem_controls._refined:
                self.fm_controls.undo_refine_btn.setEnabled(True)
            else:
                self.fm_controls.undo_refine_btn.setEnabled(False)

        if self.fm_controls.other.show_merge:
            self.fm_controls.progress_bar.setValue(100)
        else:
            self.fm_controls.progress_bar.setValue(0)
        if self.fm_controls.other._refined:
            self.fm_controls.err_btn.setText('x: \u00B1{:.2f}, y: \u00B1{:.2f}'.format(self.fm_controls.other._std[idx][0],
                                                                           self.fm_controls.other._std[idx][1]))
        else:
            self.fm_controls.err_btn.setText('0')

            #if self.fib_controls.num_slices is None:
            #    self.fib_controls.num_slices = self.fm_controls.num_slices
            #    if self.fib_controls.ops is not None:
            #        if self.fib_controls.ops.fib_matrix is not None and self.fm_controls.num_slices is not None:
            #            self.fib_controls.correct_grid_z()

        if self.fm_controls is not None and self.fm_controls.ops is not None:
            if self.fm_controls.ops._transformed:
                self.fm_controls.other.size_box.setEnabled(True)
                self.fm_controls.other.auto_opt_btn.setEnabled(True)

    @utils.wait_cursor('print')
    def _show_scatter(self, idx):
        if idx == 0:
            self.scatter = Scatter(self, self.sem_controls, self.print)
        else:
            self.scatter = Scatter(self, self.fib_controls, self.print)
        self.scatter.show()

    @utils.wait_cursor('print')
    def _show_convergence(self, idx):
        if len(self.fm_controls.other._conv[idx]) == 3:
            if idx == 0:
                self.convergence = Convergence(self, self.sem_controls, self.print)
            else:
                self.convergence = Convergence(self, self.fib_controls, self.print)
            self.convergence.show()
        else:
            self.print('To use this feature, you have to use at least 10 points for the refinement!')

    @utils.wait_cursor('print')
    def _show_peak_params(self, state=None):
        self.fm_controls.peak_btn.setChecked(False)
        if self.peak_params is None:
            self.peak_params = Peak_Params(self, self.fm_controls, self.print, self.log)
            self.fm_controls.peak_controls = self.peak_params
        self.peak_params.show()

    @utils.wait_cursor('print')
    def merge(self, project=None):
        self.fm = self.fm_controls.ops
        self.em = self.fm_controls.other.ops
        if self.tabs.currentIndex() == 0:
            self.em = self.sem_controls.ops
            ops = self.em
            popup = self.sem_popup
            controls = self.sem_controls
        elif self.tabs.currentIndex() == 1:
            ops = self.fib_controls.sem_ops
            popup = self.fib_popup
            controls = self.fib_controls
        else:
            ops = self.tem_controls.ops
            popup = self.tem_popup
            controls = self.tem_controls

        if self.fm is not None and self.em is not None:
            if self.fib_controls.tab_index == 1 and self.fib_controls.sem_ops.data is None:
                self.print('You have to calculate the FM to TEM/SEM correlation first!')
            else:
                if self.fm._tf_points is not None and (ops._tf_points is not None or ops._tf_points_region is not None):
                    #condition = self.fm_controls.merge()
                    condition = controls.merge()
                    if condition:
                        if popup is not None:
                            popup.close()
                        popup = Merge(self, self.print, self.log)
                        controls.popup = popup
                        self.project.merged = True
                        self.project.popup = popup
                        if self.project.load_merge:
                            self.project._load_merge(project)
                            self.project.load_merge = False
                        popup.show()
                else:
                    self.print('You have to transform the FM and the TEM/SEM images first!')
        else:
            self.print('Select FM and EM data first!')

    @utils.wait_cursor('print')
    def _set_theme(self, name):
        self.setStyleSheet('')
        with open(resource_path('styles/%s.qss' % name), 'r') as f:
            self.setStyleSheet(f.read())

        if name != 'none':
            if name == 'solarized':
                c = (203, 76, 22, 80)
                bc = '#002b36'
            else:
                c = (0, 0, 255, 80)
                bc = (0, 0, 0)

            for imview in [self.fib_imview, self.sem_imview, self.fm_imview]:
                imview.view.setBackgroundColor(bc)
                hwidget = imview.getHistogramWidget()
                hwidget.setBackground(bc)
                hwidget.item.region.setBrush(c)
                hwidget.item.fillHistogram(color=c)
        self.settings.setValue('theme', name)

    def keyPressEvent(self, event):
        key = event.key()
        mod = int(event.modifiers())

        if QtGui.QKeySequence(mod + key) == QtGui.QKeySequence('Ctrl+P'):
            self._prev_file()
        elif QtGui.QKeySequence(mod + key) == QtGui.QKeySequence('Ctrl+N'):
            self._next_file()
        elif QtGui.QKeySequence(mod + key) == QtGui.QKeySequence('Ctrl+W'):
            self.close()
        else:
            event.ignore()

    def closeEvent(self, event):
        self.settings.setValue('channel_colors', self.colors)
        self.settings.setValue('geometry', self.geometry())
        self.settings.setValue('fm_folder', self.fm_controls._curr_folder)
        self.settings.setValue('sem_folder', self.sem_controls._curr_folder)
        self.settings.setValue('tem_folder', self.tem_controls._curr_folder)
        self.settings.setValue('fib_folder', self.fib_controls._curr_folder)
        self.settings.setValue('project_folder', self.project._project_folder)
        event.accept()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Clement: GUI for Correlative Light and Electron Microscopy')
    parser.add_argument('-p', '--project_fname', help='Path to project .yml file')
    parser.add_argument('--no-restore', help='Do not restore QSettings from last time Clement closed', action='store_true')
    args, unknown_args = parser.parse_known_args()

    app = QtWidgets.QApplication(unknown_args)
    app.setStyle('fusion')
    gui = GUI(args.project_fname, args.no_restore)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
