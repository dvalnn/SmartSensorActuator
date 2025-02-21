import ast
import astor
import sys
import os

def remove_docstrings(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            parsed = ast.parse(f.read())
        except SyntaxError as e:
            print(f"Skipping file {input_file} due to syntax error: {e}")
            return

    for node in ast.walk(parsed):
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)):
            continue

        if not node.body:
            continue

        if not isinstance(node.body[0], ast.Expr):
            continue

        if not hasattr(node.body[0], 'value') or not isinstance(node.body[0].value, ast.Constant):
            continue

        node.body = node.body[1:]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(astor.to_source(parsed))

def process_directory(input_dir, output_dir):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".py"):  # Process only Python files (you can adjust this)
                input_file = os.path.join(root, file)
                relative_path = os.path.relpath(input_file, input_dir)
                output_file = os.path.join(output_dir, relative_path)

                output_dir_for_file = os.path.dirname(output_file)
                os.makedirs(output_dir_for_file, exist_ok=True) # Create necessary dirs

                remove_docstrings(input_file, output_file)
                print(f"Processed: {input_file} -> {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_directory> <output_directory>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    process_directory(input_dir, output_dir)
    print(f"Finished processing files in {input_dir}")
