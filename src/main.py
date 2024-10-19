import sys
import logging
import os
import subprocess
from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QStackedWidget, QRadioButton, QSpinBox, QTextEdit, QDateEdit, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for both development and PyInstaller. """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class PageWindow(QMainWindow):
    def __init__(self, num_pages, full_name, birth_date, jmbg):
        super().__init__()

        # Load the page_window.ui file
        uic.loadUi(resource_path("page_window.ui"), self)

        # Add scrollable area and set resizable behavior
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.centralWidget())
        self.setCentralWidget(self.scroll_area)

        # Set minimum window size
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Adjust font size based on window height
        self.setAdaptiveFontSize()

        # Keep track of the number of pages and patient information
        self.num_pages = num_pages
        self.full_name = full_name
        self.birth_date = birth_date
        self.jmbg = jmbg

        # Access text input fields for both pages
        self.textInputPage1 = self.findChild(QTextEdit, "textInputPage1")
        self.textInputPage2 = self.findChild(QTextEdit, "textInputPage2")

        # Connect the textChanged signal to check line length
        self.textInputPage1.textChanged.connect(self.check_line_length)
        self.textInputPage2.textChanged.connect(self.check_line_length)

        # Access page buttons and stacked widget from the .ui file
        self.page_buttons = [self.findChild(QPushButton, f"pageButton{i+1}") for i in range(num_pages)]
        self.stacked_widget = self.findChild(QStackedWidget, "stackedWidget")

        # Access radio buttons for pages
        self.radioButtonDG_page1 = self.findChild(QRadioButton, "radioButtonDG_page1")
        self.radioButtonDGIDEM_page1 = self.findChild(QRadioButton, "radioButtonDGIDEM_page1")
        self.radioButtonDG_page2 = self.findChild(QRadioButton, "radioButtonDG_page2")
        self.radioButtonDGIDEM_page2 = self.findChild(QRadioButton, "radioButtonDGIDEM_page2")

        # Access text input fields for both pages
        self.textInputPage1 = self.findChild(QTextEdit, "textInputPage1")
        self.textInputPage2 = self.findChild(QTextEdit, "textInputPage2")

        # Access new diagnosis text input fields for both pages
        self.diagnosisInputPage1 = self.findChild(QTextEdit, "diagnosisInputPage1")
        self.diagnosisInputPage2 = self.findChild(QTextEdit, "diagnosisInputPage2")

        # Access date picker (QDateEdit) for both pages
        self.dateEditPage1 = self.findChild(QDateEdit, "dateEditPage1")
        self.dateEditPage2 = self.findChild(QDateEdit, "dateEditPage2")

        # Access submit buttons from UI
        self.log_button_page1 = self.findChild(QPushButton, "log_button_page1")
        self.log_button_page2 = self.findChild(QPushButton, "log_button_page2")

        # Hide the submit buttons initially
        self.log_button_page1.hide()
        self.log_button_page2.hide()

        # Connect submit buttons to the PDF generation function
        self.log_button_page1.clicked.connect(self.generate_pdf)
        self.log_button_page2.clicked.connect(self.generate_pdf)

        # Initially set to Page 1 and set default selections
        self.current_page = 1
        self.switch_page(1)

        # Connect buttons to switch between pages
        for i, button in enumerate(self.page_buttons):
            if button:
                button.clicked.connect(lambda _, x=i: self.switch_page(x + 1))
    
    def check_line_length(self):
        """Check if any line in QTextEdit exceeds 80 characters and highlight it."""
        sender = self.sender()  # Get the sender object (QTextEdit)
        text = sender.toPlainText()

        # Split text into lines
        lines = text.split('\n')
        background_warning = False

        for line in lines:
            if len(line) > 80:
                background_warning = True
                break

        # Change background color if line exceeds 80 characters
        if background_warning:
            sender.setStyleSheet("QTextEdit { background-color: #FFDDDD; }")  # Light red
        else:
            sender.setStyleSheet("")  # Reset to default

    def setAdaptiveFontSize(self):
        """Adjust font size based on screen resolution."""
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        font_size = max(10, screen_size.height() // 75)  # Adaptive scaling factor
        font = QFont("NotoSans", font_size)
        self.setFont(font)

    def resizeEvent(self, event):
        """Handle window resizing."""
        super().resizeEvent(event)

    def switch_page(self, page_number):
        """Switch to the selected page and update the button styles."""
        logging.info(f"Switching to Page {page_number}")
        if self.stacked_widget:
            self.current_page = page_number
            self.stacked_widget.setCurrentIndex(page_number - 1)

            # Set default radio button selections and disable others
            if page_number == 1:
                self.radioButtonDG_page1.setChecked(True)
                self.radioButtonDGIDEM_page1.setEnabled(False)
                self.radioButtonDG_page1.setStyleSheet(self.get_selected_style())
                self.radioButtonDGIDEM_page1.setStyleSheet(self.get_disabled_style())
                if self.num_pages == 1:
                    self.log_button_page1.show()
                else:
                    self.log_button_page1.hide()
                self.log_button_page2.hide()

            elif page_number == 2:
                self.radioButtonDGIDEM_page2.setChecked(True)
                self.radioButtonDG_page2.setEnabled(False)
                self.radioButtonDGIDEM_page2.setStyleSheet(self.get_selected_style())
                self.radioButtonDG_page2.setStyleSheet(self.get_disabled_style())
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

    def get_selected_style(self):
        """Return the style for the selected radio button."""
        return """
            QRadioButton {
                color: #4CAF50;  /* Green */
                font-weight: bold;
            }
        """

    def get_disabled_style(self):
        """Return the style for the disabled (unselected) radio button."""
        return """
            QRadioButton {
                color: gray;
            }
            QRadioButton::indicator {
                background-color: lightgray;
            }
        """

    def format_date(self, date_str):
        """Format date to 'dd.mm.yyyy.' format with leading zeros."""
        try:
            date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            return date_obj.strftime('%d.%m.%Y.')
        except ValueError:
            logging.error(f"Invalid date format: {date_str}")
            return date_str

    def draw_header(self, pdf_canvas, base_x, y_position, header_text):
        """Draw the header with centered alignment on the given canvas."""
        pdf_canvas.setFont("NotoSans-Bold", 12)
        max_line_width = max(pdf_canvas.stringWidth(line, "NotoSans-Bold", 12) for line in header_text)

        # Draw each line of the header text
        for line in header_text:
            line_width = pdf_canvas.stringWidth(line, "NotoSans-Bold", 12)
            offset = (max_line_width - line_width) / 2  # Calculate offset for center alignment
            pdf_canvas.drawString(base_x + offset, y_position, line)
            y_position -= 20  # Move to the next line

        return y_position

    def draw_patient_info(self, pdf_canvas, base_x, y_position):
        """Draw the patient information block."""
        pdf_canvas.setFont("NotoSans-Bold", 10)

        # Define patient information text
        patient_info = [
            f"Ime i prezime pacijenta: {self.full_name}",
            f"Datum rođenja: {self.format_date(self.birth_date)}",
            f"JMBG: {self.jmbg}"
        ]

        # Draw each line of the patient information text
        y_position -= 20  # Move the patient info a couple of rows down
        for line in patient_info:
            pdf_canvas.drawString(base_x + 10, y_position, line)
            y_position -= 15  # Move to the next line

        return y_position

    def draw_dg_table(self, pdf_canvas, base_x, y_position, dg_text):
        """Draw the DG table with two columns and respect original line breaks."""
        pdf_canvas.setFont("NotoSans-Bold", 10)
        
        # Set the starting x-position for DG
        dg_x = base_x

        # Set the initial y-position to align DG with text
        y_position -= 15  # Move down slightly to align vertically

        # Draw the "DG:" label
        pdf_canvas.drawString(dg_x, y_position, "DG:")

        # Set the starting x-position for the DG text (aligned with "DG:")
        text_x = base_x + 30  # Adjust this to align DG with the text

        # Define the maximum width for text wrapping
        max_line_width = 530  # Increase to allow more text before wrapping

        # Split the DG text by line breaks
        lines = dg_text.split('\n')

        for line in lines:
            words = line.split()
            current_line = ""
            
            for word in words:
                # Calculate the width of the current line if the word is added
                line_width = pdf_canvas.stringWidth(current_line + " " + word, "NotoSans-Bold", 10)
                
                if line_width < max_line_width:
                    # Add the word to the current line if it fits
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    # Draw the current line and start a new one
                    pdf_canvas.drawString(text_x, y_position, current_line)
                    y_position -= 15  # Move down for the next line
                    current_line = word

            # Draw any remaining text in the current line after processing words
            if current_line:
                pdf_canvas.drawString(text_x, y_position, current_line)
                y_position -= 15  # Move down for the next line

        return y_position
    
    def draw_diagnosis_content(self, pdf_canvas, base_x, y_position, diagnosis_content):
        """Draw the 'Content of Diagnosis' text below the DG table, respecting line breaks and empty lines."""
        pdf_canvas.setFont("NotoSans", 10)  # Set to regular font

        # Set the starting x-position for diagnosis content
        diagnosis_x = base_x

        # Add a gap below the DG table
        y_position -= 25  # Adjust to create some space below the DG text


        # Move down slightly to align the text with the label
        y_position -= 15

        # Define the maximum width for text wrapping
        max_line_width = 550  # Adjust this as needed to match the page layout

        # Split the diagnosis content by line breaks (including empty lines)
        lines = diagnosis_content.split('\n')

        for line in lines:
            if line.strip() == "":
                # Add space for empty lines in the input
                y_position -= 15
                continue

            words = line.split()
            current_line = ""

            for word in words:
                # Calculate the width of the current line if the word is added
                line_width = pdf_canvas.stringWidth(current_line + " " + word, "NotoSans", 10)
                
                if line_width < max_line_width:
                    # Add the word to the current line if it fits
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    # Draw the current line and start a new one
                    pdf_canvas.drawString(diagnosis_x, y_position, current_line)
                    y_position -= 15  # Move down for the next line
                    current_line = word

            # Draw any remaining text in the current line after processing words
            if current_line:
                pdf_canvas.drawString(diagnosis_x, y_position, current_line)
                y_position -= 15  # Move down for the next line

        return y_position
    
    def draw_footer(self, pdf_canvas, base_x, y_position, page_date):
        """Draw the date and doctor's information at the bottom of the page."""
        pdf_canvas.setFont("NotoSans-Bold", 10)


        # Draw the date text on the left side
        footer_left_x = base_x
        footer_left_y = y_position - 80  # Move it 4-5 lines down
        pdf_canvas.drawString(footer_left_x, footer_left_y, f"{self.format_date(page_date)} Beograd")

        # Draw the doctor's info at the bottom right, centered horizontally
        doctor_info = [
            "Dr. Svetlana Šlapek Branković",
            "Specijalista fizikalne medicine i rehabilitacije"
        ]

        max_line_width = max(pdf_canvas.stringWidth(line, "NotoSans", 10) for line in doctor_info)
        footer_right_x = A4[0] - base_x - max_line_width  # Align to the right edge
        footer_right_y = footer_left_y

        for line in doctor_info:
            line_width = pdf_canvas.stringWidth(line, "NotoSans", 10)
            offset = (max_line_width - line_width) / 2  # Center horizontally
            pdf_canvas.drawString(footer_right_x + offset, footer_right_y, line)
            footer_right_y -= 15  # Move down for the next line

        return y_position - 100  # Adjust the y-position to account for the footer height


    def generate_pdf(self):
        """Generate a PDF report based on the input data."""
        file_name = f"{self.full_name.replace(' ', '_').replace('-', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf_canvas = canvas.Canvas(file_name, pagesize=A4)
        width, height = A4

        regular_font_path = resource_path('NotoSans-Regular.ttf')
        bold_font_path = resource_path('NotoSans-Bold.ttf')

        # Register the font (use your actual font path)
        pdfmetrics.registerFont(TTFont('NotoSans', 'NotoSans-Bold.ttf'))

        # Define the string and font
        test_string = "QWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWERTYQWER"
        font_name = 'NotoSans'
        font_size = 10  # Example font size

        # Calculate the pixel width of the string
        string_width = pdfmetrics.stringWidth(test_string, font_name, font_size)

        print(f"The width of the string in pixels is: {string_width}")

        # Register the fonts
        if os.path.exists(regular_font_path) and os.path.exists(bold_font_path):
            try:
                pdfmetrics.registerFont(TTFont('NotoSans', regular_font_path))
                pdfmetrics.registerFont(TTFont('NotoSans-Bold', bold_font_path))
            except Exception as e:
                logging.error(f"Failed to register fonts: {e}")
                return
        else:
            logging.error("Font files not found.")
            return

        # Define custom margins
        top_margin = 30

        # Define the header text
        header_text = [
            "SPECIJALISTIČKA LEKARSKA ORDINACIJA",
            "IZ OBLASTI FIZIKALNE MEDICINE I REHABILITACIJE",
            "PHYSICALDOKTOR BEOGRAD"
        ]

        # Set the base x-coordinate for the header and patient info
        base_x = 25

        # Draw the header, patient info, and DG table on Page 1
        y_position = height - top_margin
        y_position = self.draw_header(pdf_canvas, base_x, y_position, header_text)
        y_position = self.draw_patient_info(pdf_canvas, base_x, y_position - 10)
        dg_text_page1 = self.textInputPage1.toPlainText() or "IDEM"
        y_position = self.draw_dg_table(pdf_canvas, base_x, y_position - 20, dg_text_page1)
        # Draw diagnosis content for Page 1
        diagnosis_content_page1 = self.diagnosisInputPage1.toPlainText()
        y_position = self.draw_diagnosis_content(pdf_canvas, base_x, y_position, diagnosis_content_page1)
        # Draw footer on Page 1
        page_date_page1 = self.dateEditPage1.date().toString('dd-MM-yyyy')
        y_position = self.draw_footer(pdf_canvas, base_x, y_position, page_date_page1)


        # Add content for Page 2 if applicable
        if self.num_pages > 1:
            pdf_canvas.showPage()

            # Draw the header, patient info, and DG table on Page 2
            y_position = height - top_margin
            y_position = self.draw_header(pdf_canvas, base_x, y_position, header_text)
            y_position = self.draw_patient_info(pdf_canvas, base_x, y_position - 10)
            dg_text_page2 = self.textInputPage2.toPlainText() or "IDEM"
            y_position = self.draw_dg_table(pdf_canvas, base_x, y_position - 20, dg_text_page2)
            # Draw diagnosis content for Page 2
            diagnosis_content_page2 = self.diagnosisInputPage2.toPlainText()
            y_position = self.draw_diagnosis_content(pdf_canvas, base_x, y_position, diagnosis_content_page2)
             # Draw footer on Page 2
            page_date_page2 = self.dateEditPage2.date().toString('dd-MM-yyyy')
            y_position = self.draw_footer(pdf_canvas, base_x, y_position, page_date_page2)


        pdf_canvas.save()
        logging.info(f"PDF report saved as {file_name}")

        # Open the generated PDF automatically
        self.open_pdf(file_name)

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

        # Add scrollable area and set resizable behavior
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.centralWidget())
        self.setCentralWidget(self.scroll_area)

        # Set minimum window size
        self.setMinimumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Adjust font size based on screen height
        self.setAdaptiveFontSize()

        # Access widgets by their object names from the .ui file
        self.page_count_box = self.findChild(QSpinBox, "pageCountBox")
        self.start_button = self.findChild(QPushButton, "startButton")
        self.name_edit = self.findChild(QTextEdit, "nameEdit")
        self.date_edit = self.findChild(QDateEdit, "dateEdit")
        self.jmbg_edit = self.findChild(QTextEdit, "jmbgEdit")

        if not self.page_count_box or not self.start_button or not self.name_edit or not self.date_edit or not self.jmbg_edit:
            logging.error("One or more widgets could not be found in the UI file.")
            return

        self.start_button.clicked.connect(self.open_page_window)

    def setAdaptiveFontSize(self):
        """Adjust font size based on screen resolution."""
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        font_size = max(10, screen_size.height() // 75)
        font = QFont("NotoSans", font_size)
        self.setFont(font)

    def resizeEvent(self, event):
        """Handle window resizing."""
        super().resizeEvent(event)


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
        self.page_window.show()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
