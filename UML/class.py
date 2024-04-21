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
        self.types = {}
        self.methods = {}

    def visit_ClassDef(self, node):
        class_name = node.name
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
        self.inheritances.extend((class_name, base) for base in bases)

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self.types[target.id] = self.infer_type(item.value)
                        if isinstance(item.value, ast.Call) and isinstance(item.value.func, ast.Name):
                            # Check if the type is a class and add to compositions or aggregations
                            called_class = item.value.func.id
                            if called_class in self.classes:
                                # If the object is instantiated inside the class, it's a composition
                                self.compositions.append((class_name, called_class))
            elif isinstance(item, ast.FunctionDef):
                self.methods[item.name] = self.infer_method_return_type(item)
        self.classes[class_name] = {'properties': list(self.types.keys()), 'methods': list(self.methods.keys())}

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

def modify_dot_content(dot_content, generator):
    # Process class definitions, type annotations, and inheritance
    lines = dot_content.split('\n')
    new_relationships = []
    for subclass, baseclass in generator.inheritances:
        new_relationships.append(f'  "temp.{baseclass}" -> "temp.{subclass}" [arrowhead="empty"];')
    for owner, part in generator.compositions:
        new_relationships.append(f'  "temp.{owner}" -> "temp.{part}" [arrowhead="diamond", style="solid"];')
    for owner, part in generator.aggregations:
        new_relationships.append(f'  "temp.{owner}" -> "temp.{part}" [arrowhead="diamond", style="dashed"];')


    for class_name, details in generator.classes.items():
        for prop in details['properties']:
            lines = [re.sub(r'(\\l)?' + re.escape(prop) + r'(\s*=\s*\S+)?(<br ALIGN="LEFT"/>)',
                            rf'\1- {prop} : {generator.types[prop]}\2\3', line) for line in lines]
        for method in details['methods']:
            lines = [re.sub(r'(\\l)?' + re.escape(method) + r'\(\)(<br ALIGN="LEFT"/>)',
                            rf'\1+ {method}() : {generator.methods[method]}\2', line) for line in lines]

    insert_index = next((i for i, line in enumerate(lines) if '}' in line), len(lines))
    lines = lines[:insert_index] + new_relationships + lines[insert_index:]
    return '\n'.join(lines)

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

# Example usage
code = """
class Engine:
    def start(self):
        print("Engine starting")

class Wheel:
    def rotate(self):
        print("Wheel rotating")

class Car:
    def __init__(self):
        self.engine = Engine()  # 컴포지션: Car가 Engine의 생명주기를 관리
        self.wheels = [Wheel() for _ in range(4)]  # 컴포지션: Car가 Wheel의 생명주기를 관리

    def drive(self):
        self.engine.start()
        for wheel in self.wheels:
            wheel.rotate()

class ElectricEngine(Engine):
    def start(self):
        print("Electric engine starting")

class ElectricCar(Car):
    def __init__(self):
        super().__init__()
        self.engine = ElectricEngine()  # 어그리게이션: ElectricCar는 ElectricEngine을 참조하지만 생명주기를 관리하지 않음

    def charge(self):
        print("Charging electric car")

"""

generate_class_diagram(code)
