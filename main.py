import os
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFileDialog, QTextEdit, QMessageBox, QHBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal
from create_database import generate_data_store  # Your existing method for processing PDFs
from query_data import get_query_result  # Your refactored method for querying data


class PDFProcessorThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, file_path=None, directory_path=None):
        super().__init__()
        self.file_path = file_path
        self.directory_path = directory_path

    def run(self):
        try:
            if self.directory_path:
                generate_data_store("", self.directory_path)
                self.finished.emit(f"Processed directory: {self.directory_path}")
            elif self.file_path:
                generate_data_store(self.file_path, "")
                self.finished.emit(f"Processed file: {self.file_path}")
        except Exception as e:
            self.finished.emit(f"Error: {e}")


class QueryThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, query_text):
        super().__init__()
        self.query_text = query_text

    def run(self):
        try:
            result = get_query_result(self.query_text)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(f"Error: {e}")


class PDFQAApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the user interface
        self.initUI()

        # Variables to hold file/directory paths
        self.file_path = None
        self.directory_path = None

    def initUI(self):
        """Initialize the UI elements."""
        self.setWindowTitle('Intelligent PDF Agent')
        self.setGeometry(100, 100, 600, 400)
        layout = QVBoxLayout()

        # Instructions label
        instructions = QLabel('Select a PDF file or a directory containing PDF files or both.', self)
        layout.addWidget(instructions)

        # File selection layout
        file_layout = QHBoxLayout()
        self.file_label = QLabel('No file selected', self)
        self.file_button = QPushButton('Choose PDF File', self)
        self.file_button.setFixedSize(150, 30)  # Smaller button
        self.file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_button)
        layout.addLayout(file_layout)

        # Directory selection layout
        directory_layout = QHBoxLayout()
        self.directory_label = QLabel('No directory selected', self)
        self.directory_button = QPushButton('Choose Directory', self)
        self.directory_button.setFixedSize(150, 30)  # Smaller button
        self.directory_button.clicked.connect(self.select_directory)
        directory_layout.addWidget(self.directory_label)
        directory_layout.addWidget(self.directory_button)
        layout.addLayout(directory_layout)

        # Query input layout
        self.query_label = QLabel('Ask a question:', self)
        self.query_input = QLineEdit(self)

        # Ask button
        self.ask_button = QPushButton('Ask Question', self)
        self.ask_button.setFixedSize(150, 30)  # Smaller button
        self.ask_button.clicked.connect(self.ask_question)

        # Answer display
        self.answer_text = QTextEdit(self)
        self.answer_text.setReadOnly(True)

        # Add elements to the layout
        layout.addWidget(self.query_label)
        layout.addWidget(self.query_input)
        layout.addWidget(self.ask_button)
        layout.addWidget(self.answer_text)

        # Exit button
        self.exit_button = QPushButton('Exit', self)
        self.exit_button.setFixedSize(150, 30)  # Smaller button
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button)

        # Set layout and style
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #f9f9f9;  /* Light background */
                border-radius: 10px;  /* Soft edges */
                padding: 20px;
            }
            QPushButton {
                background-color: #b2e0d9;  /* Soft pastel color */
                border: none;  /* Remove border */
                border-radius: 5px;  /* Soft edges */
                font-size: 14px;  /* Smaller font size */
            }
            QPushButton:hover {
                background-color: #a0d3c1;  /* Slightly darker on hover */
            }
            QLabel {
                font-size: 12px;  /* Smaller font size */
            }
            QLineEdit {
                padding: 10px;
                border-radius: 5px;  /* Soft edges */
                border: 1px solid #c0c0c0;  /* Subtle border */
            }
            QTextEdit {
                padding: 10px;
                border-radius: 5px;  /* Soft edges */
                border: 1px solid #c0c0c0;  /* Subtle border */
            }
        """)

    def select_file(self):
        """Open file dialog to select a PDF file."""
        options = QFileDialog.Options()
        self.file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "",
                                                        "PDF Files (*.pdf);;All Files (*)", options=options)
        if self.file_path:
            self.file_label.setText(f"Selected file: {self.file_path}")
            self.directory_path = None
            self.directory_label.setText("No directory selected")
            self.process_files()

    def select_directory(self):
        """Open file dialog to select a directory."""
        options = QFileDialog.Options()
        self.directory_path = QFileDialog.getExistingDirectory(self, "Select Directory", "", options=options)
        if self.directory_path:
            self.directory_label.setText(f"Selected directory: {self.directory_path}")
            self.file_path = None
            self.file_label.setText("No file selected")
            self.process_files()

    def process_files(self):
        """Process the selected file or directory into ChromaDB."""
        if not self.file_path and not self.directory_path:
            QMessageBox.warning(self, "Input Error", "Please select a PDF file or directory to process.")
            return

        # Disable buttons while processing
        self.ask_button.setEnabled(False)

        # Run the processing in a background thread
        self.thread = PDFProcessorThread(file_path=self.file_path, directory_path=self.directory_path)
        self.thread.finished.connect(self.on_processing_finished)
        self.thread.start()

    def on_processing_finished(self, message):
        """Handle completion of file processing."""
        QMessageBox.information(self, "Processing Complete", message)
        self.ask_button.setEnabled(True)

    def ask_question(self):
        """Query the vector database for answers."""
        query_text = self.query_input.text()
        if not query_text:
            QMessageBox.warning(self, "Input Error", "Please enter a question to ask.")
            return

        # Disable buttons while querying
        self.ask_button.setEnabled(False)

        # Run the query in a background thread
        self.query_thread = QueryThread(query_text=query_text)
        self.query_thread.finished.connect(self.on_query_finished)
        self.query_thread.start()

    def on_query_finished(self, result):
        """Display the query result in the answer box."""
        self.answer_text.setText(result)
        self.ask_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = PDFQAApp()
    main_window.show()
    sys.exit(app.exec_())

