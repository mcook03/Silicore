# engine/parser.py

def start_engine():
    print("Silicore analysis engine initialized")

def parse_pcb_file(file_path):
    components = []
    try:
        with open(file_path, 'r') as f:
            lines = [line for line in f if line.strip()]  # ignore blank lines
            if not lines:
                print(f"File {file_path} is empty!")
                return components
            
            header = lines[0].strip().split(',')
            for line in lines[1:]:
                values = line.strip().split(',')
                component = dict(zip(header, values))
                
                # Convert X/Y to integers
                component['x'] = int(component['x'])
                component['y'] = int(component['y'])
                
                components.append(component)
    except FileNotFoundError:
        print(f"File {file_path} not found!")
    return components