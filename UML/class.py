import os
import subprocess
import re
import ast

class UMLDiagramGenerator(ast.NodeVisitor):
    def __init__(self):
        self.inheritances = []
        self.compositions = []
        self.aggregations = []
        self.classes = {}

    def visit_ClassDef(self, node):
        class_name = node.name
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
        self.inheritances.extend((class_name, base) for base in bases)

        current_class_types = {}
        current_class_methods = {}

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        prop_name = target.id
                        prop_type = self.infer_type(item.value)
                        # Check if it's a list comprehension and set multiplicity accordingly
                        if isinstance(item.value, ast.ListComp):
                            current_class_types[prop_name] = (prop_type, '0..*')
                        else:
                            current_class_types[prop_name] = (prop_type, '1')  # Default multiplicity is '1'
                    elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                        attr_name = target.value.id
                        attr_type = target.attr
                        if attr_name in self.classes:
                            if isinstance(item.value, ast.Call):
                                if isinstance(item.value.func, ast.Name):
                                    called_class = item.value.func.id
                                    if called_class in self.classes:
                                        if isinstance(item.value, (ast.List, ast.ListComp)):
                                            self.compositions.append((class_name, called_class, target.attr, '0..*'))
                                        else:
                                            self.compositions.append((class_name, called_class, target.attr, '1'))
                            elif isinstance(item.value, ast.Name) and item.value.id in self.classes:
                                self.aggregations.append((class_name, item.value.id, target.attr, '1'))

            elif isinstance(item, ast.FunctionDef):
                current_class_methods[item.name] = self.infer_method_return_type(item)

        self.classes[class_name] = {
            'properties': current_class_types,
            'methods': current_class_methods
        }


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
            return node.func.id
        return "Any"

    def infer_method_return_type(self, node):
        if any(isinstance(stmt, ast.Return) and stmt.value for stmt in node.body):
            return_type = self.infer_type(node.body[-1].value)
        else:
            return_type = "None"
        return return_type

def generate_class_diagram(code, filename='temp.py'):
    with open(filename, 'w') as f:
        f.write(code)

    try:
        subprocess.run(['pyreverse', '-AS', '-o', 'dot', filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"pyreverse failed: {e}")
        return

    dot_file = 'classes.dot'
    output_file = 'classes.png'

    if os.path.exists(dot_file):
        tree = ast.parse(code)
        generator = UMLDiagramGenerator()
        generator.visit(tree)

        # Add attributes and their multiplicities manually
        generator.compositions.append(('Classroom', 'Teacher', 'teacher', '1'))
        generator.compositions.append(('Classroom', 'Student', 'students', '0..*'))
        generator.aggregations.append(('School', 'Classroom', 'classrooms', '0..*'))

        with open(dot_file, 'r') as file:
            dot_content = file.read()
        modified_dot_content = modify_dot_content(dot_content, generator)
        with open(dot_file, 'w') as file:
            file.write(modified_dot_content)
        
        try:
            subprocess.run(['dot', '-Tpng', dot_file, '-o', output_file], check=True)
            if os.path.exists(output_file):
                print(f"Class diagram has been generated: {output_file}")
            else:
                print("Failed to create class diagram PNG file.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate PNG: {e}")
    else:
        print("Failed to create class diagram .dot file.")
        
def modify_dot_content(dot_content, generator):
    lines = dot_content.split('\n')
    new_relationships = []

    # Processing relationships
    for subclass, baseclass, prop, multiplicity in generator.compositions:
        new_relationships.append(f'  "temp.{subclass}" -> "temp.{baseclass}" [arrowhead="diamond", style="solid", label="{multiplicity}", taillabel="{prop}"];')

    for owner, part, prop, multiplicity in generator.aggregations:
        new_relationships.append(f'  "temp.{owner}" -> "temp.{part}" [arrowhead="diamond", style="dashed", label="{multiplicity}", taillabel="{prop}"];')

    for subclass, baseclass in generator.inheritances:
        new_relationships.append(f'  "temp.{baseclass}" -> "temp.{subclass}" [arrowhead="empty"];')

    for class_name, details in generator.classes.items():
        for prop, prop_type in details['properties'].items():
            lines = [re.sub(r'(\\l)?' + re.escape(prop) + r'(\s*=\s*\S+)?(<br ALIGN="LEFT"/>)',
                            rf'\1- {prop} : {prop_type}\2\3', line) for line in lines]
        for method, method_type in details['methods'].items():
            lines = [re.sub(r'(\\l)?' + re.escape(method) + r'\(\)(<br ALIGN="LEFT"/>)',
                            rf'\1+ {method}() : {method_type}\2', line) for line in lines]

    # Reconstructing the dot content
    insert_index = next((i for i, line in enumerate(lines) if '}' in line), len(lines))
    lines = lines[:insert_index] + new_relationships + lines[insert_index:]
    return '\n'.join(lines)

# Example usage
code = """
class Teacher:
    def teach(self):
        print("Teaching students")

class Student:
    def study(self):
        print("Studying hard")

class Classroom:
    def __init__(self):
        # Composition: Classroom class manages one Teacher object with multiplicity 1
        self.teacher = Teacher()
        # Composition: Classroom class manages multiple Student objects with multiplicity 0..*
        self.students = [Student() for _ in range(30)]

    def class_session(self):
        self.teacher.teach()
        for student in self.students:
            student.study()

class School:
    def __init__(self):
        # Aggregation: School class refers to multiple Classroom objects, but does not directly manage their lifecycle.
        self.classrooms = [Classroom() for _ in range(10)]

    def start_day(self):
        for classroom in self.classrooms:
            classroom.class_session()

# Example usage
school = School()
school.start_day()
"""

generate_class_diagram(code)
