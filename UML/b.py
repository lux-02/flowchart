import os
import subprocess
import re

def generate_class_diagram(code, filename='temp.py'):
    with open(filename, 'w') as f:
        f.write(code)
    
    # Run pyreverse to generate .dot file instead of png
    try:
        subprocess.run(['pyreverse', '-AS', '-o', 'dot', filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"pyreverse failed: {e.stderr}")
        return
    
    dot_file = 'classes.dot'
    output_file = 'classes.png'
    
    # Check if .dot file exists and proceed
    if os.path.exists(dot_file):
        modify_dot_file(dot_file)
        # Generate PNG from the modified .dot file using dot command
        subprocess.run(['dot', '-Tpng', dot_file, '-o', output_file], check=True)
        if os.path.exists(output_file):
            print(f"Class diagram has been generated: {output_file}")
        else:
            print("Failed to create class diagram PNG file.")
    else:
        print("Failed to create class diagram .dot file.")


def modify_dot_file(dot_file):
    with open(dot_file, 'r') as file:
        dot_content = file.read()

    # Modify the content of .dot file
    modified_dot_content = modify_dot_content(dot_content)
    
    with open(dot_file, 'w') as file:
        file.write(modified_dot_content)

def modify_dot_content(content):
    # Add types and default values for attributes
    content = re.sub(r'(\\l)?(\w+)(<br ALIGN="LEFT"/>)', r'\1- \2 : String = ""\3', content)
    # Add return types for methods
    content = re.sub(r'(\\l)?(\w+)\(\)(<br ALIGN="LEFT"/>)', r'\1+ \2() : None\3', content)
    
    return content

# Example usage
code = """
class Course:
    def __init__(self):
        self.students = []  # List of Student instances

    def add_student(self, student):
        assert isinstance(student, Student), "Only Student instances can be added."
        self.students.append(student)

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        print(f"Hello, my name is {self.name} and I am {self.age} years old.")

class Student(Person):
    def __init__(self, name, age, student_id):
        super().__init__(name, age)
        self.student_id = student_id

    def study(self):
        print(f"Student {self.name} is studying.")
"""

generate_class_diagram(code)
