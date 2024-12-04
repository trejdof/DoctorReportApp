import sys
import logging
import os
import subprocess
import json
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QStackedWidget, QSpinBox, QTextEdit,
    QDateEdit, QScrollArea, QSizePolicy, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QTextOption, QFontDatabase, QFontMetrics
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def resource_path(relative_path):
    """Get the absolute path to a resource, works for both development and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_config():
    """Load configuration from a JSON file."""
    config_path = resource_path('config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        return {}

class PageWindow(QMainWindow):
    def __init__(self, num_pages, full_name, birth_date, jmbg):
        super().__init__()

        self.errors = {}

        # Load the page_window.ui file
        uic.loadUi(resource_path("page_window.ui"), self)

        # Load the configuration data
        self.config = load_config()

        # Access text input fields for both pages
        self.textInputPage1 = self.findChild(QTextEdit, "textInputPage1")
        self.diagnosisInputPage1 = self.findChild(QTextEdit, "diagnosisInputPage1")
        self.textInputPage2 = self.findChild(QTextEdit, "textInputPage2") if num_pages > 1 else None
        self.diagnosisInputPage2 = self.findChild(QTextEdit, "diagnosisInputPage2") if num_pages > 1 else None

        # Load the monospaced fonts
        monospaced_font_path = resource_path('fonts/NotoSansMono-Regular.ttf')
        monospaced_bold_font_path = resource_path('fonts/NotoSansMono-Bold.ttf')

        # Load the regular font
        font_id_regular = QFontDatabase.addApplicationFont(monospaced_font_path)
        if font_id_regular == -1:
            logging.error("Failed to load Noto Sans Mono Regular font.")
        else:
            logging.info("Noto Sans Mono Regular font loaded successfully.")

        # Load the bold font
        font_id_bold = QFontDatabase.addApplicationFont(monospaced_bold_font_path)
        if font_id_bold == -1:
            logging.error("Failed to load Noto Sans Mono Bold font.")
        else:
            logging.info("Noto Sans Mono Bold font loaded successfully.")

        # Retrieve the font family names
        font_family_regular = QFontDatabase.applicationFontFamilies(font_id_regular)[0]
        font_family_bold = QFontDatabase.applicationFontFamilies(font_id_bold)[0]

        # Create QFont objects
        fixed_font_size = 12  # Fixed font size
        font_regular = QFont(font_family_regular, fixed_font_size)
        font_bold = QFont(font_family_bold, fixed_font_size)

        # Store fonts for later use
        self.font_regular = font_regular
        self.font_bold = font_bold

        # Set the fonts to your QTextEdit widgets
        self.textInputPage1.setFont(font_regular)
        self.diagnosisInputPage1.setFont(font_regular)
        if self.textInputPage2:
            self.textInputPage2.setFont(font_regular)
        if self.diagnosisInputPage2:
            self.diagnosisInputPage2.setFont(font_regular)

        # Set tab stop distance (for handling tabs)
        tab_stop_distance = 40  # Adjust as needed
        self.diagnosisInputPage1.setTabStopDistance(tab_stop_distance)
        if self.diagnosisInputPage2:
            self.diagnosisInputPage2.setTabStopDistance(tab_stop_distance)

        # Set word wrap mode to allow wrapping at word boundaries
        self.diagnosisInputPage1.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        if self.diagnosisInputPage2:
            self.diagnosisInputPage2.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.textInputPage1.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        if self.textInputPage2:
            self.textInputPage2.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)

        # Register fonts in ReportLab
        if os.path.exists(monospaced_font_path) and os.path.exists(monospaced_bold_font_path):
            try:
                pdfmetrics.registerFont(TTFont('NotoSansMono', monospaced_font_path))
                pdfmetrics.registerFont(TTFont('NotoSansMono-Bold', monospaced_bold_font_path))
                logging.info("Monospaced fonts registered successfully.")
            except Exception as e:
                logging.error(f"Failed to register monospaced fonts: {e}")
        else:
            logging.error("Monospaced font files not found.")

        # Set maximum characters per line
        self.max_chars_per_line_dg_table = 71
        self.max_chars_per_line_diagnosis = 89

        # Calculate the character width in the GUI (font size 12)
        font_metrics = QFontMetrics(font_regular)
        char_width_gui = font_metrics.horizontalAdvance('A')

        # Set the fixed width of the DG table input boxes
        self.textInputPage1.setFixedWidth(self.max_chars_per_line_dg_table * char_width_gui + char_width_gui + char_width_gui + char_width_gui)
        if self.textInputPage2:
            self.textInputPage2.setFixedWidth(self.max_chars_per_line_dg_table * char_width_gui + char_width_gui + char_width_gui + char_width_gui)

        # Set the fixed width of the diagnosis content input boxes
        self.diagnosisInputPage1.setFixedWidth(self.max_chars_per_line_diagnosis * char_width_gui + char_width_gui + char_width_gui + char_width_gui)
        if self.diagnosisInputPage2:
            self.diagnosisInputPage2.setFixedWidth(self.max_chars_per_line_diagnosis * char_width_gui + char_width_gui + char_width_gui + char_width_gui)

        # Add scrollable area and set resizable behavior
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.centralWidget())
        self.setCentralWidget(self.scroll_area)

        # Set minimum window size
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Keep track of the number of pages and patient information
        self.num_pages = num_pages
        self.full_name = full_name
        self.birth_date = birth_date
        self.jmbg = jmbg

        # Define margins
        self.base_x = 25  # Left margin
        self.right_margin = 25  # Right margin

        # Access page buttons and stacked widget from the .ui file
        self.page_buttons = [self.findChild(QPushButton, f"pageButton{i+1}") for i in range(num_pages)]
        self.stacked_widget = self.findChild(QStackedWidget, "stackedWidget")

        # Access date picker (QDateEdit) for both pages
        self.dateEditPage1 = self.findChild(QDateEdit, "dateEditPage1")
        self.dateEditPage2 = self.findChild(QDateEdit, "dateEditPage2") if num_pages > 1 else None

        # Set date pickers to current date
        current_date = QDate.currentDate()
        self.dateEditPage1.setDate(current_date)
        if self.dateEditPage2:
            self.dateEditPage2.setDate(current_date)

        # Access submit buttons from UI
        self.log_button_page1 = self.findChild(QPushButton, "log_button_page1")
        self.log_button_page2 = self.findChild(QPushButton, "log_button_page2") if num_pages > 1 else None

        # Hide the submit buttons initially
        self.log_button_page1.hide()
        if self.log_button_page2:
            self.log_button_page2.hide()

        # Connect submit buttons to the PDF generation function
        self.log_button_page1.clicked.connect(self.generate_pdf)
        if self.log_button_page2:
            self.log_button_page2.clicked.connect(self.generate_pdf)

        # Initially set to Page 1 and set default selections
        self.current_page = 1
        self.switch_page(1)

        # Connect buttons to switch between pages
        for i, button in enumerate(self.page_buttons):
            if button:
                button.clicked.connect(lambda _, x=i: self.switch_page(x + 1))

        # Connect textChanged signals to the check methods
        self.textInputPage1.textChanged.connect(self.check_textInputPage1)
        self.diagnosisInputPage1.textChanged.connect(self.check_diagnosisInputPage1)
        if self.num_pages > 1 and self.textInputPage2:
            self.textInputPage2.textChanged.connect(self.check_textInputPage2)
        if self.num_pages > 1 and self.diagnosisInputPage2:
            self.diagnosisInputPage2.textChanged.connect(self.check_diagnosisInputPage2)

    def switch_page(self, page_number):
        """Switch to the selected page and update the button styles."""
        logging.info(f"Switching to Page {page_number}")
        if self.stacked_widget:
            self.current_page = page_number
            self.stacked_widget.setCurrentIndex(page_number - 1)

            if page_number == 1:
                if self.num_pages == 1:
                    self.log_button_page1.show()
                else:
                    self.log_button_page1.hide()
                if self.log_button_page2:
                    self.log_button_page2.hide()
            elif page_number == 2:
                if self.log_button_page2:
                    self.log_button_page2.show()
                self.log_button_page1.hide()

            if self.num_pages == 1:
                self.log_button_page1.show()

            self.update_button_styles()

    def update_button_styles(self):
        """Update the styles of the buttons to show which one is active."""
        for i, button in enumerate(self.page_buttons):
            if button:
                if i + 1 == self.current_page:
                    button.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            border: 2px solid #2E7D32;
                            font-weight: bold;
                            padding: 10px;
                        }
                    """)
                else:
                    button.setStyleSheet("""
                        QPushButton {
                            background-color: #E0E0E0;
                            color: black;
                            border: 1px solid #9E9E9E;
                            padding: 10px;
                        }
                    """)

    def format_date(self, date_str):
        """Format date to 'dd.mm.yyyy.' format with leading zeros."""
        try:
            date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            return date_obj.strftime('%d.%m.%Y.')
        except ValueError:
            logging.error(f"Invalid date format: {date_str}")
            return date_str

    def draw_header(self, pdf_canvas, y_position):
        """Draw the header with centered alignment using data from the JSON file."""
        # Load header text from the config
        header_text = self.config.get("header", ["Default Header"])

        pdf_canvas.setFont("NotoSansMono-Bold", 12)
        max_line_width = max(pdf_canvas.stringWidth(line, "NotoSansMono-Bold", 12) for line in header_text)

        for line in header_text:
            line_width = pdf_canvas.stringWidth(line, "NotoSansMono-Bold", 12)
            offset = (max_line_width - line_width) / 2
            pdf_canvas.drawString(self.base_x + offset, y_position, line)
            y_position -= 20

        return y_position

    def draw_patient_info(self, pdf_canvas, y_position):
        """Draw the patient information block."""
        pdf_canvas.setFont("NotoSansMono-Bold", 12)

        # Define patient information text
        patient_info = [
            f"Ime i prezime pacijenta: {self.full_name}",
            f"Datum rođenja: {self.format_date(self.birth_date)}",
            f"JMBG: {self.jmbg}"
        ]

        # Draw each line of the patient information text
        y_position -= 20  # Move the patient info a couple of rows down
        for line in patient_info:
            pdf_canvas.drawString(self.base_x + 10, y_position, line)
            y_position -= 15  # Move to the next line

        return y_position

    def draw_dg_table(self, pdf_canvas, y_position, dg_text):
        """Draw the DG table with two columns and respect original line breaks."""
        pdf_canvas.setFont("NotoSansMono-Bold", 12)

        # Get page width from the canvas
        width, height = pdf_canvas._pagesize

        # Set the starting x-position for DG
        dg_x = self.base_x

        # Set the initial y-position to align DG with text
        y_position -= 15  # Move down slightly to align vertically

        # Draw the "DG:" label
        pdf_canvas.drawString(dg_x, y_position, "DG:")

        # Set the starting x-position for the DG text (aligned with "DG:")
        text_x = self.base_x + 30  # Adjust this to align DG with the text

        # Define the maximum width for text wrapping
        max_line_width = width - self.base_x - self.right_margin - (text_x - self.base_x)

        # Split the DG text by line breaks
        lines = dg_text.split('\n')

        for line in lines:
            if line.strip() == "":
                # Add space for empty lines in the input
                y_position -= 15
                continue

            # Wrap the line manually based on character limit
            while len(line) > self.max_chars_per_line_dg_table:
                to_draw = line[:self.max_chars_per_line_dg_table]
                pdf_canvas.drawString(text_x, y_position, to_draw)
                y_position -= 15  # Move down for the next line
                line = line[self.max_chars_per_line_dg_table:]
            # Draw the remaining part
            pdf_canvas.drawString(text_x, y_position, line)
            y_position -= 15  # Move down for the next line

        return y_position

    def draw_diagnosis_content(self, pdf_canvas, y_position, text_edit):
        """Draw the 'Content of Diagnosis' text, matching QTextEdit's displayed lines."""
        # Set font
        font_size = 10  # The font size used in the PDF
        pdf_canvas.setFont("NotoSansMono", font_size)

        # Define a custom line spacing factor for the PDF
        line_spacing_factor = 1.5  # Adjust this value as needed

        # Calculate line height based on font size and line spacing factor
        line_height = font_size * line_spacing_factor

        # Add initial empty line
        y_position -= 1 * line_height

        # Retrieve text from QTextEdit and expand tabs
        text_content = text_edit.toPlainText().expandtabs(tabsize=4)  # You can adjust tabsize as needed
        displayed_lines = text_content.split('\n')

        # Draw each line
        for line in displayed_lines:
            # Wrap the line manually based on character limit
            while len(line) > self.max_chars_per_line_diagnosis:
                to_draw = line[:self.max_chars_per_line_diagnosis]
                pdf_canvas.drawString(self.base_x, y_position, to_draw)
                y_position -= line_height
                line = line[self.max_chars_per_line_diagnosis:]
            # Draw the remaining part
            pdf_canvas.drawString(self.base_x, y_position, line)
            y_position -= line_height

        return y_position

    def draw_footer(self, pdf_canvas, y_position, page_date):
        """Draw the date and doctor's information at the bottom of the page using data from the JSON file."""
        pdf_canvas.setFont("NotoSansMono-Bold", 10)

        # Draw the date text on the left side
        footer_left_x = self.base_x
        footer_left_y = y_position - 20  # Move it 4-5 lines down
        pdf_canvas.drawString(footer_left_x, footer_left_y, f"{self.format_date(page_date)} Beograd")

        # Load the footer information from the configuration file
        footer_info = self.config.get("footer", ["Default Doctor Info"])
        max_line_width = max(pdf_canvas.stringWidth(line, "NotoSansMono-Bold", 10) for line in footer_info)

        # Align the footer info to the right side
        footer_right_x = A4[0] - self.base_x - max_line_width
        footer_right_y = footer_left_y

        # Draw each line of the footer information
        for line in footer_info:
            line_width = pdf_canvas.stringWidth(line, "NotoSansMono-Bold", 10)
            offset = (max_line_width - line_width) / 2  # Center horizontally
            pdf_canvas.drawString(footer_right_x + offset, footer_right_y, line)
            footer_right_y -= 15  # Move down for the next line

        return y_position - 100  # Adjust the y-position to account for the footer height

    def check_textInputPage1(self):
        self.check_input_length(self.textInputPage1, self.max_chars_per_line_dg_table, 'textInputPage1')

    def check_diagnosisInputPage1(self):
        self.check_input_length(self.diagnosisInputPage1, self.max_chars_per_line_diagnosis, 'diagnosisInputPage1')

    def check_textInputPage2(self):
        if self.textInputPage2:
            self.check_input_length(self.textInputPage2, self.max_chars_per_line_dg_table, 'textInputPage2')

    def check_diagnosisInputPage2(self):
        if self.diagnosisInputPage2:
            self.check_input_length(self.diagnosisInputPage2, self.max_chars_per_line_diagnosis, 'diagnosisInputPage2')

    def check_input_length(self, text_edit, max_chars_per_line, key):
        """Check the length of each line in the text_edit and update error state."""
        # Expand tabs in the text
        text = text_edit.toPlainText().expandtabs(tabsize=4)
        lines = text.split('\n')
        error = False
        for line in lines:
            if len(line) > max_chars_per_line:
                error = True
                break
        if error:
            # Set the border of text_edit to red and display a message
            text_edit.setStyleSheet("border: 2px solid red;")
            text_edit.setToolTip("Line exceeds maximum length; please continue on the next line.")
            self.errors[key] = True  # Set error state for this field
        else:
            # Reset the border
            text_edit.setStyleSheet("")
            text_edit.setToolTip("")
            self.errors[key] = False  # Clear error state for this field


    def generate_pdf(self):
        """Generate a PDF report based on the input data."""
        if any(self.errors.values()):
            logging.error("Cannot generate PDF: One or more input fields exceed the allowed limit.")
            # Display a popup message to the user
            QMessageBox.warning(
                self,
                "Greška",
                "Nije moguće generisati izveštaj, neka od linija u crvenom polju je duža nego što bi smelo."
            )
            return

        # Create the /izvestaji/ folder if it doesn't exist
        pdf_output_folder = os.path.join(os.getcwd(), 'izvestaji')
        if not os.path.exists(pdf_output_folder):
            os.makedirs(pdf_output_folder)

        # Generate the PDF file name with the /izvestaji/ directory
        pdf_file_name = os.path.join(pdf_output_folder, f"{self.full_name.replace(' ', '_').replace('-', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf")

        # Generate the TXT file name in the current working directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        txt_file_name = f"{self.full_name.replace(' ', '_').replace('-', '_')}_{timestamp}.txt"

        # Register fonts in ReportLab
        monospaced_font_path = resource_path('fonts/NotoSansMono-Regular.ttf')
        monospaced_bold_font_path = resource_path('fonts/NotoSansMono-Bold.ttf')

        if os.path.exists(monospaced_font_path) and os.path.exists(monospaced_bold_font_path):
            try:
                pdfmetrics.registerFont(TTFont('NotoSansMono', monospaced_font_path))
                pdfmetrics.registerFont(TTFont('NotoSansMono-Bold', monospaced_bold_font_path))
                logging.info("Monospaced fonts registered successfully.")
            except Exception as e:
                logging.error(f"Failed to register monospaced fonts: {e}")
                return
        else:
            logging.error("Monospaced font files not found.")
            return

        pdf_canvas = canvas.Canvas(pdf_file_name, pagesize=A4)
        width, height = A4

        # Draw the header, patient info, and DG table on Page 1
        y_position = height - 30  # Adjust top margin
        y_position = self.draw_header(pdf_canvas, y_position)
        y_position = self.draw_patient_info(pdf_canvas, y_position - 10)
        dg_text_page1 = self.textInputPage1.toPlainText() or "IDEM"
        y_position = self.draw_dg_table(pdf_canvas, y_position - 20, dg_text_page1)
        # Draw diagnosis content for Page 1
        y_position = self.draw_diagnosis_content(pdf_canvas, y_position, self.diagnosisInputPage1)
        # Draw footer on Page 1
        page_date_page1 = self.dateEditPage1.date().toString('dd-MM-yyyy')
        y_position = self.draw_footer(pdf_canvas, y_position, page_date_page1)

        # Initialize variables for Page 2 content
        dg_text_page2 = None
        diagnosis_content_page2 = None

        # Add content for Page 2 if applicable
        if self.num_pages > 1:
            pdf_canvas.showPage()

            # Draw the header, patient info, and DG table on Page 2
            y_position = height - 30  # Adjust top margin
            y_position = self.draw_header(pdf_canvas, y_position)
            y_position = self.draw_patient_info(pdf_canvas, y_position - 10)
            dg_text_page2 = self.textInputPage2.toPlainText() or "IDEM"
            y_position = self.draw_dg_table(pdf_canvas, y_position - 20, dg_text_page2)
            # Draw diagnosis content for Page 2
            y_position = self.draw_diagnosis_content(pdf_canvas, y_position, self.diagnosisInputPage2)
            # Draw footer on Page 2
            page_date_page2 = self.dateEditPage2.date().toString('dd-MM-yyyy')
            y_position = self.draw_footer(pdf_canvas, y_position, page_date_page2)

        pdf_canvas.save()
        logging.info(f"PDF report saved as {pdf_file_name}")

        # Save content to a .txt file in the current working directory
        diagnosis_content_page1 = self.diagnosisInputPage1.toPlainText()
        if self.num_pages > 1:
            diagnosis_content_page2 = self.diagnosisInputPage2.toPlainText()
        self.save_content_to_txt(txt_file_name, dg_text_page1, diagnosis_content_page1, dg_text_page2, diagnosis_content_page2)

        # Open the generated PDF automatically
        self.open_pdf(pdf_file_name)

    def save_content_to_txt(self, txt_file_name, dg_text_page1, diagnosis_content_page1, dg_text_page2=None, diagnosis_content_page2=None):
        """Save the DG and diagnosis content to a .txt file in the /txt/ subfolder."""
        txt_folder = "txt"
        os.makedirs(txt_folder, exist_ok=True)
        txt_file_path = os.path.join(txt_folder, txt_file_name)

        try:
            with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write("Page 1 - DG:\n")
                txt_file.write(dg_text_page1 + "\n\n")
                txt_file.write("Page 1 - Diagnosis Content:\n")
                txt_file.write(diagnosis_content_page1 + "\n\n")

                if dg_text_page2 and diagnosis_content_page2:
                    txt_file.write("Page 2 - DG:\n")
                    txt_file.write(dg_text_page2 + "\n\n")
                    txt_file.write("Page 2 - Diagnosis Content:\n")
                    txt_file.write(diagnosis_content_page2 + "\n\n")

            logging.info(f"Content saved to {txt_file_path}")
        except Exception as e:
            logging.error(f"Failed to save content to .txt file: {e}")

    def open_pdf(self, file_name):
        """Open the generated PDF file automatically."""
        try:
            if sys.platform == "win32":
                os.startfile(file_name)
            elif sys.platform == "darwin":
                subprocess.run(["open", file_name])
            else:
                subprocess.run(["xdg-open", file_name])
        except Exception as e:
            logging.error(f"Failed to open PDF: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load the main_window.ui file
        uic.loadUi(resource_path("main_window.ui"), self)

        # Load the monospaced fonts
        monospaced_font_path = resource_path('fonts/NotoSansMono-Regular.ttf')
        monospaced_bold_font_path = resource_path('fonts/NotoSansMono-Bold.ttf')

        # Load the regular font
        font_id_regular = QFontDatabase.addApplicationFont(monospaced_font_path)
        if font_id_regular == -1:
            logging.error("Failed to load Noto Sans Mono Regular font.")
        else:
            logging.info("Noto Sans Mono Regular font loaded successfully.")

        # Retrieve the font family names
        font_family_regular = QFontDatabase.applicationFontFamilies(font_id_regular)[0]

        # Create QFont objects
        fixed_font_size = 12  # Fixed font size
        font_regular = QFont(font_family_regular, fixed_font_size)

        # Add scrollable area and set resizable behavior
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.centralWidget())
        self.setCentralWidget(self.scroll_area)

        # Set minimum window size
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Access widgets by their object names from the .ui file
        self.page_count_box = self.findChild(QSpinBox, "pageCountBox")
        self.start_button = self.findChild(QPushButton, "startButton")
        self.name_edit = self.findChild(QTextEdit, "nameEdit")
        self.date_edit = self.findChild(QDateEdit, "dateEdit")
        self.jmbg_edit = self.findChild(QTextEdit, "jmbgEdit")

        if not self.page_count_box or not self.start_button or not self.name_edit or not self.date_edit or not self.jmbg_edit:
            logging.error("One or more widgets could not be found in the UI file.")
            return

        # Set the fonts to your QTextEdit widgets
        self.name_edit.setFont(font_regular)
        self.jmbg_edit.setFont(font_regular)

        # Set the date_edit to current date
        current_date = QDate.currentDate()
        self.date_edit.setDate(current_date)

        self.start_button.clicked.connect(self.open_page_window)

    def open_page_window(self):
        """Open the page window based on the number of pages."""
        num_pages = self.page_count_box.value()

        # Get the full name, birth date, and JMBG from inputs
        full_name = self.name_edit.toPlainText().strip()
        birth_date = self.date_edit.date().toString('dd-MM-yyyy')
        jmbg = self.jmbg_edit.toPlainText().strip()

        logging.info(f"Number of Pages: {num_pages}, Name: {full_name}, Birth Date: {birth_date}, JMBG: {jmbg}")

        # Open the page window with the specified number of pages and patient information
        self.page_window = PageWindow(num_pages, full_name, birth_date, jmbg)

        # Hide the second page button if only one page is selected
        if num_pages == 1:
            # Hide the "pageButton2"
            page_button_2 = self.page_window.findChild(QPushButton, "pageButton2")
            if page_button_2:
                page_button_2.hide()

        self.page_window.show()

def main():
    # Set application attributes before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_Use96Dpi, True)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
