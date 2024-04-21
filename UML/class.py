import os
import subprocess
import re
import ast

class TypeInferencer(ast.NodeVisitor):
    def __init__(self):
        self.types = {}
        self.methods = {}

    def visit_ClassDef(self, node):
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.methods[item.name] = self.infer_method_return_type(item)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self.types[target.id] = self.infer_type(item.value)

    def infer_type(self, node):
        if isinstance(node, ast.List):
            return "List"
        elif isinstance(node, ast.Dict):
            return "Dict"
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return "String"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id  # Assume it's a constructor call
        return "Any"

    def infer_method_return_type(self, node):
        if any(isinstance(stmt, ast.Return) and stmt.value for stmt in node.body):
            return_type = self.infer_type(node.body[-1].value)
        else:
            return_type = "None"
        return return_type

def parse_code_and_infer_types(code):
    tree = ast.parse(code)
    inferencer = TypeInferencer()
    inferencer.visit(tree)
    return inferencer.types, inferencer.methods

def modify_dot_content(content, types, methods):
    for var, typ in types.items():
        content = re.sub(r'(\\l)?' + re.escape(var) + r'(\s*=\s*\S+)?(<br ALIGN="LEFT"/>)',
                         rf'\1- {var} : {typ}\2\3', content)
    for method, return_type in methods.items():
        content = re.sub(r'(\\l)?' + re.escape(method) + r'\(\)(<br ALIGN="LEFT"/>)',
                         rf'\1+ {method}() : {return_type}\2', content)
    return content

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
        types, methods = parse_code_and_infer_types(code)
        modify_dot_file(dot_file, types, methods)
        # Generate PNG from the modified .dot file using dot command
        subprocess.run(['dot', '-Tpng', dot_file, '-o', output_file], check=True)
        if os.path.exists(output_file):
            print(f"Class diagram has been generated: {output_file}")
        else:
            print("Failed to create class diagram PNG file.")
    else:
        print("Failed to create class diagram .dot file.")

def modify_dot_file(dot_file, types, methods):
    with open(dot_file, 'r') as file:
        dot_content = file.read()

    modified_dot_content = modify_dot_content(dot_content, types, methods)
    with open(dot_file, 'w') as file:
        file.write(modified_dot_content)

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
        return "studying"
"""

generate_class_diagram(code)
