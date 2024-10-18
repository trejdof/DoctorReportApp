import sys
import logging
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QStackedWidget, QRadioButton, QSpinBox, QTextEdit, QDateEdit
from PyQt5.QtCore import Qt

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PageWindow(QMainWindow):
    def __init__(self, num_pages):
        super().__init__()

        # Load the page_window.ui file
        uic.loadUi("page_window.ui", self)

        # Keep track of the number of pages
        self.num_pages = num_pages

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

        # Connect submit buttons to logging function
        self.log_button_page1.clicked.connect(self.log_selections)
        self.log_button_page2.clicked.connect(self.log_selections)

        # Initially set to Page 1 and set default selections
        self.current_page = 1
        self.switch_page(1)  # Ensure initial defaults are applied

        # Connect buttons to switch between pages
        for i, button in enumerate(self.page_buttons):
            if button:
                button.clicked.connect(lambda _, x=i: self.switch_page(x + 1))

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
                    self.log_button_page1.show()  # Show submit button on page 1 if only one page exists
                else:
                    self.log_button_page1.hide()  # Hide if there's a second page
                self.log_button_page2.hide()

            elif page_number == 2:
                # Make sure DG IDEM is selected on Page 2 and styled properly
                self.radioButtonDGIDEM_page2.setChecked(True)
                self.radioButtonDG_page2.setEnabled(False)
                self.radioButtonDGIDEM_page2.setStyleSheet(self.get_selected_style())
                self.radioButtonDG_page2.setStyleSheet(self.get_disabled_style())
                self.log_button_page2.show()  # Show submit button only on last page
                self.log_button_page1.hide()  # Hide submit button on page 1

            # If there's only one page, show the submit button on Page 1
            if self.num_pages == 1:
                self.log_button_page1.show()

            self.update_button_styles()

    def update_button_styles(self):
        """Update the styles of the buttons to show which one is active."""
        for i, button in enumerate(self.page_buttons):
            if button:
                if i + 1 == self.current_page:
                    # Active button style
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
                    # Inactive button style
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

    def log_selections(self):
        """Log the selections from both the main window and the page content."""
        logging.info("Submitting the report...")

        # Log Page 1 selections
        if self.radioButtonDG_page1.isChecked():
            logging.info("Page 1 selected: DG")
        elif self.radioButtonDGIDEM_page1.isChecked():
            logging.info("Page 1 selected: DG IDEM")

        logging.info(f"Page 1 text input: {self.textInputPage1.toPlainText()}")
        logging.info(f"Page 1 diagnosis content: {self.diagnosisInputPage1.toPlainText()}")
        logging.info(f"Page 1 date selected: {self.dateEditPage1.date().toString('dd-MM-yyyy')}")

        # Log Page 2 selections (if applicable)
        if self.num_pages > 1:
            if self.radioButtonDG_page2.isChecked():
                logging.info("Page 2 selected: DG")
            elif self.radioButtonDGIDEM_page2.isChecked():
                logging.info("Page 2 selected: DG IDEM")

            logging.info(f"Page 2 text input: {self.textInputPage2.toPlainText()}")
            logging.info(f"Page 2 diagnosis content: {self.diagnosisInputPage2.toPlainText()}")
            logging.info(f"Page 2 date selected: {self.dateEditPage2.date().toString('dd-MM-yyyy')}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load the main_window.ui file
        uic.loadUi("main_window.ui", self)

        # Access widgets by their object names from the .ui file
        self.page_count_box = self.findChild(QSpinBox, "pageCountBox")
        self.start_button = self.findChild(QPushButton, "startButton")

        # Check if widgets are found
        if not self.page_count_box or not self.start_button:
            logging.error("One or more widgets could not be found in the UI file.")
            return

        # Connect the button to open page window
        self.start_button.clicked.connect(self.open_page_window)

    def open_page_window(self):
        """Open the page window based on the number of pages."""
        num_pages = self.page_count_box.value()
        logging.info(f"Number of Pages: {num_pages}")

        # Open the page window with the specified number of pages
        self.page_window = PageWindow(num_pages)
        self.page_window.show()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
