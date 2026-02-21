from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QTabWidget
)
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

        self.generate_btn = QPushButton("Generate Dummy Jobs")
        self.generate_btn.clicked.connect(self.generate_data)

        self.table = QTableWidget()

        layout.addWidget(self.generate_btn)
        layout.addWidget(self.table)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Job Listings")

    def generate_data(self):
        generate_dummy_jobs(200)
        self.load_jobs()

    def load_jobs(self):
        jobs = self.db.fetch_all_jobs()
        self.table.setRowCount(len(jobs))
        self.table.setColumnCount(9)

        headers = ["ID", "Title", "Company", "Location",
                   "Salary", "Experience", "Skills", "Job Type", "Posted Date"]

        self.table.setHorizontalHeaderLabels(headers)

        for row_idx, job in enumerate(jobs):
            for col_idx, value in enumerate(job):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))