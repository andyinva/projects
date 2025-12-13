"""
APPEND THIS TO THE END OF dialogs.py

Additional dialogs for group and subject management.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QTextEdit, QDialogButtonBox, QMessageBox)


class GroupDialog(QDialog):
    """
    Dialog for creating or editing study groups.
    
    Provides input fields for:
    - Group name (required, unique)
    - Description (optional)
    
    Modes:
    - "create": Create new group
    - "edit": Edit existing group
    
    Example:
        >>> dialog = GroupDialog(self, mode="create")
        >>> if dialog.exec():
        ...     name, description = dialog.get_values()
        ...     controller.create_group(name, description)
    """
    
    def __init__(self, parent=None, group_name="", description="", mode="create"):
        """
        Initialize the group dialog.
        
        Args:
            parent (QWidget, optional): Parent window
            group_name (str): Initial group name (for edit mode)
            description (str): Initial description (for edit mode)
            mode (str): "create" or "edit"
            
        Side Effects:
            - Creates modal dialog window
            - Blocks parent window until closed
        """
        super().__init__(parent)
        
        self.mode = mode
        self.setWindowTitle("Create Group" if mode == "create" else "Edit Group")
        self.setMinimumWidth(400)
        
        self.setup_ui(group_name, description)
        
    def setup_ui(self, group_name, description):
        """
        Create the dialog user interface.
        
        Args:
            group_name (str): Initial group name value
            description (str): Initial description value
            
        Layout structure:
        - Title bar (from QDialog)
        - Group name label and input (single line)
        - Description label and input (multi-line)
        - OK / Cancel buttons
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Group name input (required)
        name_label = QLabel("Group Name: (required)")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setText(group_name)
        self.name_input.setPlaceholderText("e.g., New Testament, Pauline Epistles")
        layout.addWidget(self.name_input)
        
        # Description input (optional)
        desc_label = QLabel("Description: (optional)")
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlainText(description)
        self.description_input.setPlaceholderText("Optional description for this group...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)
        
        # OK/Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to name input
        self.name_input.setFocus()
        
    def validate_and_accept(self):
        """
        Validate input and accept dialog if valid.
        
        Validation rules:
        - Group name cannot be empty
        - Group name cannot be only whitespace
        
        Side Effects:
            - Shows error message if validation fails
            - Accepts dialog if validation passes
        """
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Group name cannot be empty."
            )
            self.name_input.setFocus()
            return
            
        self.accept()
        
    def get_values(self):
        """
        Get the entered group name and description.
        
        Returns:
            tuple: (name, description) both as stripped strings
            
        Example:
            >>> if dialog.exec():
            ...     name, description = dialog.get_values()
            ...     print(f"Creating group: {name}")
        """
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        return (name, description)


class SubjectDialog(QDialog):
    """
    Dialog for creating or editing study subjects.
    
    Provides input fields for:
    - Subject name (required, unique within group)
    - Description (optional)
    
    Modes:
    - "create": Create new subject
    - "edit": Edit existing subject
    
    Example:
        >>> dialog = SubjectDialog(self, mode="create")
        >>> if dialog.exec():
        ...     name, description = dialog.get_values()
        ...     controller.create_subject(name, description)
    """
    
    def __init__(self, parent=None, subject_name="", description="", mode="create"):
        """
        Initialize the subject dialog.
        
        Args:
            parent (QWidget, optional): Parent window
            subject_name (str): Initial subject name (for edit mode)
            description (str): Initial description (for edit mode)
            mode (str): "create" or "edit"
            
        Side Effects:
            - Creates modal dialog window
            - Blocks parent window until closed
        """
        super().__init__(parent)
        
        self.mode = mode
        self.setWindowTitle("Create Subject" if mode == "create" else "Edit Subject")
        self.setMinimumWidth(400)
        
        self.setup_ui(subject_name, description)
        
    def setup_ui(self, subject_name, description):
        """
        Create the dialog user interface.
        
        Args:
            subject_name (str): Initial subject name value
            description (str): Initial description value
            
        Layout structure:
        - Title bar (from QDialog)
        - Subject name label and input (single line)
        - Description label and input (multi-line)
        - OK / Cancel buttons
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Subject name input (required)
        name_label = QLabel("Subject Name: (required)")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setText(subject_name)
        self.name_input.setPlaceholderText("e.g., Prayer, Faith, Grace")
        layout.addWidget(self.name_input)
        
        # Description input (optional)
        desc_label = QLabel("Description: (optional)")
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlainText(description)
        self.description_input.setPlaceholderText("Optional description for this subject...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)
        
        # OK/Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to name input
        self.name_input.setFocus()
        
    def validate_and_accept(self):
        """
        Validate input and accept dialog if valid.
        
        Validation rules:
        - Subject name cannot be empty
        - Subject name cannot be only whitespace
        
        Side Effects:
            - Shows error message if validation fails
            - Accepts dialog if validation passes
        """
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Subject name cannot be empty."
            )
            self.name_input.setFocus()
            return
            
        self.accept()
        
    def get_values(self):
        """
        Get the entered subject name and description.
        
        Returns:
            tuple: (name, description) both as stripped strings
            
        Example:
            >>> if dialog.exec():
            ...     name, description = dialog.get_values()
            ...     print(f"Creating subject: {name}")
        """
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        return (name, description)


# END OF ADDITIONS TO dialogs.py
