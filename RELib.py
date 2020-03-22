from Bio.Restriction import AllEnzymes, CommOnly
from Bio.Restriction.Restriction import RestrictionType as rt
from Bio.Seq import complement

import sys
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QCheckBox, QDialog, QGroupBox, QLabel, QLineEdit, \
    QListWidget, QTableView, QPushButton, QRadioButton, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import QSortFilterProxyModel, QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QStandardItem, QStandardItemModel

import icons_rc

from math import log


class RELibrary(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Restriction Enzyme Library')
        self.setWindowIcon(QIcon(':icons/relib.png'))
        self.setMinimumHeight(600)

        # Generate data to fill table (default: all enzymes)
        self.data(enzyme_range=AllEnzymes)

        self.table = QTableView()
        # Do not allow editing of cells
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStyleSheet("QHeaderView {font-weight: bold}")
        self.table.verticalHeader().setStyleSheet("QHeaderView {font-weight: bold}")
        self.table.verticalHeader().sectionClicked.connect(self.OK)
        # Set default row height
        self.table.verticalHeader().setDefaultSectionSize(20)
        # Set fixed width/height for columns/rows
        self.table.horizontalHeader().setSectionResizeMode(2)
        self.table.verticalHeader().setSectionResizeMode(2)

        self.model = QStandardItemModel(self)

        self.model.setHorizontalHeaderLabels(self.header)

        # Set QToolTip font-family
        self.setStyleSheet('QToolTip {font-family: Lucida Console}')

        self.update_table()

        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)

        self.table.setModel(self.proxy)

        self.table.resizeColumnsToContents()
        self.table.verticalHeader().setFixedWidth(125)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Hide 'filtering' column (i.e. last column)
        self.table.setColumnHidden(self.model.columnCount() - 1, True)
        # Filter by last (hidden) column (enzyme name)
        self.proxy.setFilterKeyColumn(self.model.columnCount() - 1)

        self.table.setFixedWidth(980)
        self.table.setStyleSheet('gridline-color: black')

        self.search_group = QGroupBox('Search')
        self.searchL = QHBoxLayout()
        self.search_label = QLabel('Input:')
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.proxy.setFilterRegExp)
        self.searchL.addWidget(self.search_label)
        self.searchL.addWidget(self.search_input)
        self.search_group.setLayout(self.searchL)

        self.selectionL = QVBoxLayout()
        self.selection_group = QGroupBox('Selection')
        self.selection_group.setLayout(self.selectionL)
        self.selection_list = QListWidget()
        self.selectionL.addWidget(self.selection_list)

        self.enzyme_rangeL = QVBoxLayout()
        self.enzyme_range_group = QGroupBox('Enzymes')
        self.enzyme_range_group.setLayout(self.enzyme_rangeL)
        self.enzyme_range_all = QRadioButton('All')
        # Set default to 'All' enzymes
        self.enzyme_range_all.setChecked(True)
        self.enzyme_range_all.toggled.connect(self.update_enzyme_range)
        self.enzyme_range_all.setToolTip('All enzymes')
        self.enzyme_range_common = QRadioButton('Common')
        self.enzyme_range_common.toggled.connect(self.update_enzyme_range)
        self.enzyme_range_common.setToolTip('Enzymes with a commercial supplier')
        self.enzyme_rangeL.addWidget(self.enzyme_range_all)
        self.enzyme_rangeL.addWidget(self.enzyme_range_common)

        self.master_param = QWidget()
        self.master_paramL = QVBoxLayout()

        self.master_library = QWidget()
        self.master_libraryL = QVBoxLayout()
        self.library_vboxL = QVBoxLayout()
        self.library_group = QGroupBox('Library')
        self.library_group.setLayout(self.library_vboxL)

        self.library_vboxL.addWidget(self.table)

        self.buttonsW = QWidget()
        self.buttonsL = QVBoxLayout()
        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.OK)
        self.buttonsL.addWidget(self.ok_button)
        self.buttonsW.setLayout(self.buttonsL)

        self.master_paramL.addWidget(self.search_group)
        self.master_paramL.addWidget(self.selection_group)
        self.master_paramL.addWidget(self.enzyme_range_group)
        self.master_paramL.addWidget(self.buttonsW)
        self.master_param.setLayout(self.master_paramL)
        self.master_param.setFixedWidth(180)

        self.master_libraryL.addWidget(self.library_group)
        self.master_library.setLayout(self.master_libraryL)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.master_param)
        self.layout.addWidget(self.master_library)
        self.setLayout(self.layout)

    def update_table(self):
        for index, (enzyme, data) in enumerate(self.enzymes_dict.items()):
            item = [QStandardItem(str(column)) for column in data]

            # This column will be hidden (solely used for filtering)
            item += [QStandardItem(enzyme)]
            self.model.invisibleRootItem().appendRow(item)

            # Set row label (i.e. enzyme)
            row_label = QStandardItem(enzyme)
            row_label.setToolTip(self.tooltip_vheader(enzyme))
            self.model.setVerticalHeaderItem(index, row_label)

            self.tooltip_data(item)
            self.tooltip_format(item)

    def data(self, enzyme_range):
        # Create a list from the 'AllEnzymes' variable
        # included in the Bio.Restriction package
        self.enzymes = list(enzyme_range)
        self.enzymes_dict = {rt.__str__(enz): [
            enz.elucidate(),  # Recognition site and cuttings.
            rt.__len__(enz),  # Length of recognition site.
            enz.is_blunt(),  # True if the enzyme produces blunt end.
            enz.is_3overhang(),  # True if the enzyme produces 3' overhang sticky end.
            enz.is_5overhang(),  # True if the enzyme produces 5' overhang sticky end.
            enz.is_unknown(),  # True if the sequence is unknown.
            int(enz.frequency()),  # Frequency of the site given as 'one cut per x bases' (int).
            enz.is_defined(),  # True if the sequence recognised and cut is constant.
            enz.is_ambiguous(),  # True if the sequence recognised and cut is ambiguous.
            enz.is_methylable(),  # True if the recognition site is a methylable.
            enz.is_comm()  # Return if enzyme is commercially available.
            # enz.supplier_list(),	# All the suppliers of restriction enzyme.
        ]
            for enz in self.enzymes}

        # Sort dictionary by keys
        self.enzymes_dict = dict(sorted(self.enzymes_dict.items()))

        # Remove enzymes with undefined restriction site (i.e. not yet implemented in Biopython)
        self.enzymes_dict = {key: val for key, val in self.enzymes_dict.items() if
                             val[0] != 'cut twice, not yet implemented sorry.'}

        self.header = ['Recognition\nsite', 'Site\nlength', 'Blunt', "3' overhang",
                       "5' overhang", 'Known\noverhang', 'Frequency', 'Defined',
                       'Ambiguous', 'Methylable', 'Commercially\navailable']

        length = [i[1] for i in self.enzymes_dict.values()]
        self.max_length, self.min_length = log(max(length)), log(min(length))

        freq = [i[6] for i in self.enzymes_dict.values()]
        self.max_freq, self.min_freq = log(max(freq)), log(min(freq))

    def tooltip_vheader(self, enzyme):
        string = '<p>'
        for i, j in zip(self.header, self.enzymes_dict[enzyme]):
            # Default font color
            font_color = 'black'
            if j is True:
                font_color = 'green'
            if j is False:
                font_color = 'red'
            j = str('<font color="{}">{}</font>'.format(font_color, j))
            # If we reach last annotation, don't add a breakline
            if i == 'Commercially\navailable':
                string += str(i) + ': ' + j + '</font>'
            else:
                string += str(i) + ': ' + j + '</font><br/>'
        string += '</p>'

        return string

    def tooltip_data(self, item):
        # Get 'Restriction site' column only
        res_site, res_text = item[0], item[0].text()
        # If blunt
        if '^_' in res_text:
            # Add cut type (i.e. blunt) to tooltip
            tooltip = '<font color="green"><b>Blunt</b></font>'

            cut_position = res_text.find('^_')
            tooltip += '<br/>' + '&nbsp;' * cut_position + u'\u25BC' + '<br/>'
            processed = res_text.replace('^_', '|') + '<br/>'
            tooltip += processed
            tooltip += '&nbsp;' * cut_position + '+' + '<br/>'
            tooltip += complement(processed) + '<br/>' + '&nbsp;' * cut_position + u'\u25B2'

            res_site.setToolTip(tooltip)

        # Else if not blunt (i.e. sticky)
        elif '^' in res_text:
            cut_position_5, cut_position_3 = res_text.find('^'), res_text.find('_')
            # Add cut type (i.e. blunt) to tooltip
            tooltip = '<font color="red"><b>Sticky</b></font>'
            # If first cut happens on 5'
            if cut_position_3 > cut_position_5:
                diff = abs(cut_position_5 - cut_position_3) - 2
                tooltip += '<br/>' + '&nbsp;' * cut_position_5 + u'\u25BC' + '<br/>'
                processed_5, processed_3 = res_text.replace('^', '|').replace('_', '') + '<br/>', res_text.replace('_',
                                                                                                                   '|').replace(
                    '^', '') + '<br/>'
                tooltip += processed_5
                tooltip += '&nbsp;' * cut_position_5 + '+' + '-' * diff + '+' + '<br/>'
                tooltip += complement(processed_3) + '<br/>' + '&nbsp;' * (cut_position_3 - 1) + u'\u25B2'

            # If first cut happens on 3'
            else:
                diff = abs(cut_position_3 - cut_position_5) - 2
                tooltip += '<br/>' + '&nbsp;' * (cut_position_5 - 1) + u'\u25BC' + '<br/>'
                processed_5, processed_3 = res_text.replace('^', '|').replace('_', '') + '<br/>', res_text.replace('_',
                                                                                                                   '|').replace(
                    '^', '') + '<br/>'
                tooltip += processed_5
                tooltip += '&nbsp;' * cut_position_3 + '+' + '-' * diff + '+' + '<br/>'
                tooltip += complement(processed_3) + '<br/>' + '&nbsp;' * (cut_position_3) + u'\u25B2'

            res_site.setToolTip(tooltip)

    def tooltip_format(self, item):
        for col, i in enumerate(item):
            if col == 0:
                i.setFont(QFont('Lucida Console'))
            if col != 0:
                i.setTextAlignment(Qt.AlignCenter)
            # Columns with boolean values
            if col in [2, 3, 4, 5, 7, 8, 9, 10]:
                if i.text() == 'True':
                    color = QColor('#00BA38')
                    color.setAlpha(120)
                    i.setBackground(QBrush(color))
                elif i.text() == 'False':
                    color = QColor('#F8766D')
                    color.setAlpha(120)
                    i.setBackground(QBrush(color))
            # Columns with integers (normalised colouring)
            if col in [1]:
                # Set different alpha values for 'royalblue' (log normalized)
                # (200 instead of 255; looks better)
                scaling = int(log(float(i.text())) / self.max_length * 200)
                color = QColor('#619CFF')
                color.setAlpha(scaling)
                i.setBackground(QBrush(color))

            if col in [6]:
                # Set different alpha values for 'royalblue' (log normalized)
                # (200 instead of 255; looks better)
                scaling = int(log(float(i.text())) / self.max_freq * 200)
                color = QColor('#619CFF')
                color.setAlpha(scaling)
                i.setBackground(QBrush(color))

    def update_filter(self):
        params_settings = {'params_{}_check'.format(i): j for i, j in
                           zip(['blunt', '3over', '5over', 'unknown', 'defined', 'ambiguous', 'methylable'],
                               [2, 3, 4, 5, 7, 8, 9])}
        for widget, column in params_settings.items():
            if getattr(self, widget).isChecked():
                print(widget, column)
                self.proxy.setFilterKeyColumn(column)
                self.proxy.setFilterRegExp('True')
            if not self.params_blunt_check.isChecked():
                # Reset filter
                self.proxy.setFilterKeyColumn(self.model.columnCount() - 1)
                self.proxy.setFilterRegExp('')

    def OK(self):
        selected_rows = self.table.selectionModel().selectedRows()
        self.selected = set([list(self.enzymes_dict.keys())[i.row()] for i in selected_rows])

        # Clear selection list before adding values (i.e. avoid duplicates)
        self.selection_list.clear()
        self.selection_list.addItems(self.selected)
        print(self.selected)

    def update_enzyme_range(self):
        # Clear model to recreate it with new enzyme range
        self.model.removeRows(0, self.model.rowCount())
        if self.enzyme_range_all.isChecked():
            self.data(enzyme_range=AllEnzymes)
        if self.enzyme_range_common.isChecked():
            self.data(enzyme_range=CommOnly)
        # Update table
        self.update_table()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    RELib = RELibrary()
    RELib.show()
    sys.exit(app.exec_())
