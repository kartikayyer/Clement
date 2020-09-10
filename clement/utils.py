from PyQt5 import QtWidgets, QtGui, QtCore

def wait_cursor(func):
    def wrapper(*args, **kwargs):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            func(*args, **kwargs)
        except:
            QtWidgets.QApplication.restoreOverrideCursor()
            raise
        QtWidgets.QApplication.restoreOverrideCursor()
    return wrapper

def add_montage_line(parent, vbox, type_str, downsampling=False):
    line = QtWidgets.QHBoxLayout()
    vbox.addLayout(line)
    button = QtWidgets.QPushButton('Load %s Image:'%type_str, parent)
    button.clicked.connect(parent._load_mrc)
    line.addWidget(button)
    parent.mrc_fname = QtWidgets.QLabel(parent)
    line.addWidget(parent.mrc_fname, stretch=1)

    if downsampling:
        line = QtWidgets.QHBoxLayout()
        vbox.addLayout(line)
        step_label = QtWidgets.QLabel(parent)
        step_label.setText('Downsampling factor:')
        parent.step_box = QtWidgets.QLineEdit(parent)
        parent.step_box.setMaximumWidth(30)
        parent.step_box.setText('10')
        parent.step_box.setEnabled(False)
        parent._downsampling = parent.step_box.text()
        line.addWidget(step_label)
        line.addWidget(parent.step_box)
        line.addStretch(1)
        parent.assemble_btn = QtWidgets.QPushButton('Assemble', parent)
        parent.assemble_btn.clicked.connect(parent._assemble_mrc)
        parent.assemble_btn.setEnabled(False)
        line.addWidget(parent.assemble_btn)
    parent.transp_btn = QtWidgets.QCheckBox('Transpose', parent)
    parent.transp_btn.clicked.connect(parent._transpose)
    parent.transp_btn.setEnabled(False)
    line.addWidget(parent.transp_btn)

def add_fmpeaks_line(parent, vbox):
    line = QtWidgets.QHBoxLayout()
    vbox.addLayout(line)
    label = QtWidgets.QLabel('Peaks:')
    line.addWidget(label)
    parent.show_peaks_btn = QtWidgets.QCheckBox('Show FM peaks',parent)
    parent.show_peaks_btn.setEnabled(True)
    parent.show_peaks_btn.setChecked(False)
    parent.show_peaks_btn.stateChanged.connect(parent._show_FM_peaks)
    parent.show_peaks_btn.setEnabled(False)
    line.addWidget(parent.show_peaks_btn)
    label = QtWidgets.QLabel('Translation:', parent)
    line.addWidget(label)
    parent.translate_peaks_btn = QtWidgets.QPushButton('Collective', parent)
    parent.translate_peaks_btn.setCheckable(True)
    parent.translate_peaks_btn.setChecked(False)
    parent.translate_peaks_btn.toggled.connect(parent._translate_peaks)
    parent.translate_peaks_btn.setEnabled(False)
    line.addWidget(parent.translate_peaks_btn)
    parent.refine_peaks_btn = QtWidgets.QPushButton('Individual', parent)
    parent.refine_peaks_btn.setCheckable(True)
    parent.refine_peaks_btn.setChecked(False)
    parent.refine_peaks_btn.toggled.connect(parent._refine_peaks)
    parent.refine_peaks_btn.setEnabled(False)
    line.addWidget(parent.refine_peaks_btn)
    line.addStretch(1)

def add_precision_line(parent, vbox):
    line = QtWidgets.QHBoxLayout()
    vbox.addLayout(line)
    label = QtWidgets.QLabel('Refinement precision [nm]:', parent)
    line.addWidget(label)
    parent.err_btn = QtWidgets.QLabel('0')
    parent.err_plt_btn = QtWidgets.QPushButton('Show error distribution')
    parent.err_plt_btn.setEnabled(False)

    parent.convergence_btn = QtWidgets.QPushButton('Show RMS convergence')
    parent.convergence_btn.setEnabled(False)
    line.addWidget(parent.err_btn)
    line.addWidget(parent.err_plt_btn)
    line.addWidget(parent.convergence_btn)
    line.addStretch(1)

def add_define_grid_line(parent, vbox):
    line = QtWidgets.QHBoxLayout()
    vbox.addLayout(line)
    label = QtWidgets.QLabel('Grid:', parent)
    line.addWidget(label)
    parent.define_btn = QtWidgets.QPushButton('Define grid square', parent)
    parent.define_btn.setCheckable(True)
    parent.define_btn.toggled.connect(parent._define_grid_toggled)
    parent.define_btn.setEnabled(False)
    line.addWidget(parent.define_btn)
    parent.show_grid_btn = QtWidgets.QCheckBox('Show grid square', parent)
    parent.show_grid_btn.setEnabled(False)
    parent.show_grid_btn.setChecked(False)
    parent.show_grid_btn.stateChanged.connect(parent._show_grid)
    line.addWidget(parent.show_grid_btn)
    line.addStretch(1)

def add_transform_grid_line(parent, vbox, show_original=True):
    line = QtWidgets.QHBoxLayout()
    vbox.addLayout(line)
    label = QtWidgets.QLabel('Transformations:', parent)
    line.addWidget(label)
    parent.transform_btn = QtWidgets.QPushButton('Transform image', parent)
    parent.transform_btn.clicked.connect(parent._affine_transform)
    parent.transform_btn.setEnabled(False)
    line.addWidget(parent.transform_btn)
    parent.rot_transform_btn = QtWidgets.QCheckBox('Disable Shearing', parent)
    parent.rot_transform_btn.setEnabled(False)
    line.addWidget(parent.rot_transform_btn)
    if show_original:
        parent.show_btn = QtWidgets.QCheckBox('Show original data', parent)
        parent.show_btn.setEnabled(False)
        parent.show_btn.setChecked(True)
        parent.show_btn.stateChanged.connect(parent._show_original)
        line.addWidget(parent.show_btn)
        line.addStretch(1)
    return line

