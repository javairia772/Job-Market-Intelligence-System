from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QTabWidget,
    QHBoxLayout, QComboBox, QLabel
)
from sorting.sorting_algorithms import sort_jobs
from database.db_manager import DatabaseManager
from utils.dummy_data import generate_dummy_jobs


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Job Market Intelligence System")
        self.setGeometry(200, 100, 1000, 600)

        self.db = DatabaseManager()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.create_job_tab()

    def create_job_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Generate button
        self.generate_btn = QPushButton("Generate Dummy Jobs")
        self.generate_btn.clicked.connect(self.generate_data)

        # Sorting Controls
        sort_layout = QHBoxLayout()

        self.column_selector = QComboBox()
        self.column_selector.addItems([
            "ID", "Title", "Company", "Location",
            "Salary", "Experience", "Skills",
            "Job Type", "Posted Date"
        ])

        self.algorithm_selector = QComboBox()
        self.algorithm_selector.addItems([
            "Quick Sort",
            "Merge Sort",
            "Bubble Sort",
            "Tim Sort"
        ])

        self.sort_btn = QPushButton("Sort")
        self.sort_btn.clicked.connect(self.sort_data)

        self.time_label = QLabel("Execution Time: 0 ms")

        sort_layout.addWidget(self.column_selector)
        sort_layout.addWidget(self.algorithm_selector)
        sort_layout.addWidget(self.sort_btn)
        sort_layout.addWidget(self.time_label)

        self.table = QTableWidget()

        layout.addWidget(self.generate_btn)
        layout.addLayout(sort_layout)
        layout.addWidget(self.table)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Job Listings")

    def generate_data(self):
        generate_dummy_jobs(200)
        jobs = self.db.fetch_all_jobs()
        self.display_jobs(jobs)

    def display_jobs(self, jobs):
        self.table.setRowCount(len(jobs))
        self.table.setColumnCount(9)

        headers = ["ID", "Title", "Company", "Location",
                "Salary", "Experience", "Skills", "Job Type", "Posted Date"]

        self.table.setHorizontalHeaderLabels(headers)

        for row_idx, job in enumerate(jobs):
            for col_idx, value in enumerate(job):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))


    def sort_data(self):
        jobs = self.db.fetch_all_jobs()
        column = self.column_selector.currentText()
        algorithm = self.algorithm_selector.currentText()

        sorted_jobs, exec_time = sort_jobs(jobs, column, algorithm)

        self.display_jobs(sorted_jobs)

        self.time_label.setText(f"Execution Time: {round(exec_time*1000, 3)} ms")