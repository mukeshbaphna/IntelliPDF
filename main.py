import os
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFileDialog, QTextEdit, QHBoxLayout, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from create_database import generate_data_store  # Your existing method for processing PDFs
from query_data import get_response  # Your refactored method for querying data


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
            result = get_response(self.query_text)
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

        # File selection layout
        file_layout = QHBoxLayout()
        self.file_label = QLabel('Select File(s)', self)
        self.file_label.setFont(QFont('Arial', 12, QFont.Bold))  # Larger, bold font
        self.file_label.setStyleSheet('color: #00FF7F;')  # Set font color to bright green

        self.select_button = QPushButton('Select File(s)', self)
        self.select_button.setFixedSize(160, 40)
        self.select_button.clicked.connect(self.select_files_or_directory)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_button)
        layout.addLayout(file_layout)

        # Query input layout
        self.query_label = QLabel('Ask a question:', self)
        self.query_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.query_label.setStyleSheet('color: #00FF7F;')  # Set font color to bright green

        self.query_input = QLineEdit(self)
        self.query_input.returnPressed.connect(self.ask_question)
        self.query_input.setFont(QFont('Arial', 16))
        self.query_input.setStyleSheet("""
            background-color: #202020;
            border: 1px solid #00FF7F;
            color: #00FF7F;  /* Set font color to bright green */
            padding: 10px;
            border-radius: 5px;
        """)

        # Answer display
        self.answer_text = QTextEdit(self)
        self.answer_text.setReadOnly(True)
        self.answer_text.setFont(QFont('Arial', 16, QFont.Bold))
        self.answer_text.setStyleSheet("""
            background-color: #202020;
            border: 2px solid #00FF7F;
            color: #00FF7F;  /* Set font color to bright green */
            padding: 15px;
            border-radius: 5px;
        """)

        # Add elements to the layout
        layout.addWidget(self.query_label)
        layout.addWidget(self.query_input)
        layout.addWidget(self.answer_text)

        # Set layout and style
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #1C1C1C;  /* Darker background for high contrast */
                color: white;
                padding: 20px;
            }
            QPushButton {
                background-color: #2E8B57;  /* Dark green button */
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 10px;
                border: 2px solid #00FF7F;
            }
            QPushButton:hover {
                background-color: #3CB371;  /* Lighter green on hover */
            }
            QLabel {
                font-size: 16px;
                color: #00FF7F;  /* Bright green text */
            }
        """)

        # Add shadow effects to buttons and text areas
        self.add_shadow(self.select_button)
        self.add_shadow(self.query_input)
        self.add_shadow(self.answer_text)

    def add_shadow(self, widget):
        """Adds shadow to a given widget."""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(5)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 180))  # Semi-transparent black shadow
        widget.setGraphicsEffect(shadow)

    def select_files_or_directory(self):
        """Allow the user to select either a file or directory."""
        options = QFileDialog.Options()
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setOptions(options)

        if file_dialog.exec_():
            selected_items = file_dialog.selectedFiles()

            # Check if it's a directory or file
            if os.path.isdir(selected_items[0]):
                self.directory_path = selected_items[0]
                self.file_path = None
                self.file_label.setText(f"Selected directory: {self.directory_path}")
            else:
                self.file_path = selected_items[0]
                self.directory_path = None
                self.file_label.setText(f"Selected file: {self.file_path}")

            # Trigger file processing
            self.process_files()

    def process_files(self):
        """Process the selected file or directory into ChromaDB."""
        if not self.file_path and not self.directory_path:
            self.answer_text.setText("Please select a PDF file or directory to process.")
            return

        # Run the processing in a background thread
        self.thread = PDFProcessorThread(file_path=self.file_path, directory_path=self.directory_path)
        self.thread.finished.connect(self.on_processing_finished)
        self.thread.start()

    def on_processing_finished(self, message):
        """Handle completion of file processing."""
        self.answer_text.append(message)

    def ask_question(self):
        """Query the vector database for answers."""
        query_text = self.query_input.text()
        if not query_text:
            self.answer_text.setText("Please enter a question to ask.")
            return

        # Run the query in a background thread
        self.query_thread = QueryThread(query_text=query_text)
        self.query_thread.finished.connect(self.on_query_finished)
        self.query_thread.start()

    def on_query_finished(self, result):
        """Display the query result in the answer box."""
        self.answer_text.setText(result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = PDFQAApp()
    main_window.show()
    sys.exit(app.exec_())

