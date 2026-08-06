#!/usr/bin/env python3
import os
import json
import jinja2

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Resolve the config drop-zone dynamically, falling back to the default
    config_path = os.environ.get('METACLAW_CONFIG')
    if not config_path:
        config_path = os.path.abspath(os.path.join(repo_root, '..', 'config'))

    hw_json_path = os.path.join(config_path, 'data', 'hardware.json')
    if not os.path.exists(hw_json_path):
        print(f"Error: Could not find {hw_json_path}")
        return

    with open(hw_json_path, 'r', encoding='utf-8') as f:
        hardware_data = json.load(f)

    template_dir = os.path.join(repo_root, 'docs', 'personal')

    # Initialize Jinja2 environment
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

    try:
        template = env.get_template('Wade.md.j2')
    except jinja2.exceptions.TemplateNotFound:
        print("Error: Could not find Wade.md.j2 template.")
        return

    # Render the markdown file using the hardware payload
    output_md = template.render(hardware=hardware_data)

    output_path = os.path.join(template_dir, 'Wade.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_md)

    print(f"Successfully rendered {output_path} from hardware.json data.")

if __name__ == "__main__":
    main()

